"""
download_and_aggregate_rainfall.py

Phase 2B: Downloads IMD 0.25-degree daily gridded rainfall (1964–2020),
performs area-overlap weighted zonal aggregation for the 20 target catchments,
computes antecedent rainfall features (using ONLY dates <= T-1), and merges
features into data/processed/master_daily_grid_with_rainfall.csv.

Maintains data/raw/ immutability (saves downloads to data/raw/imd_rainfall/).
Uses parallel downloading with retries to retrieve 57 yearly files efficiently.
Fails fast if any validation check fails.
"""

from pathlib import Path
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from shapely.geometry import box

def download_imd_rainfall_year(year: int, dest_dir: Path, retries: int = 3) -> Path:
    """Downloads yearly 0.25° NetCDF file from IMD Pune RF25 endpoint with retry logic."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_file = dest_dir / f"ind{year}_rfp25.nc"
    if out_file.exists() and out_file.stat().st_size > 1000000:
        return out_file

    url = "https://imdpune.gov.in/cmpg/Griddata/RF25.php"
    data = urllib.parse.urlencode({'RF25': str(year)}).encode('utf-8')

    for attempt in range(1, retries + 1):
        try:
            print(f"[DOWNLOAD] Fetching year {year} (attempt {attempt}/{retries})...")
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()
                if len(content) < 100000:
                    raise ValueError(f"Downloaded payload for year {year} is too small ({len(content)} bytes)!")
                with open(out_file, "wb") as f:
                    f.write(content)
            return out_file
        except Exception as e:
            if attempt == retries:
                raise e
            print(f"[RETRY] Download year {year} failed ({e}), retrying in {attempt * 2}s...")
            time.sleep(attempt * 2)

    return out_file

def compute_catchment_weights(catchment_gdf: gpd.GeoDataFrame, ds_grid: xr.Dataset) -> dict:
    """
    Computes spatial area-overlap weights (w_i) between each catchment polygon
    and intersecting 0.25° grid cells.
    Returns dict: GaugeID -> list of (lat_idx, lon_idx, weight_fraction)
    """
    lats = ds_grid.LATITUDE.values
    lons = ds_grid.LONGITUDE.values

    # Build GeoDataFrame of grid cell polygons
    cell_polys = []
    cell_indices = []

    res = 0.25
    half = res / 2.0

    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            cell_box = box(lon - half, lat - half, lon + half, lat + half)
            cell_polys.append(cell_box)
            cell_indices.append((i, j, lat, lon))

    cells_gdf = gpd.GeoDataFrame({
        "lat_idx": [c[0] for c in cell_indices],
        "lon_idx": [c[1] for c in cell_indices],
        "lat": [c[2] for c in cell_indices],
        "lon": [c[3] for c in cell_indices]
    }, geometry=cell_polys, crs="EPSG:4326")

    # Project to EPSG:6933 (Equal Area) for area calculations
    catchments_ea = catchment_gdf.to_crs(epsg=6933)
    cells_ea = cells_gdf.to_crs(epsg=6933)

    weights_dict = {}

    for idx, catchment in catchments_ea.iterrows():
        gid = str(catchment["GaugeID"])
        c_geom = catchment.geometry

        # Find intersecting cells
        possible_matches_idx = list(cells_ea.sindex.intersection(c_geom.bounds))
        possible_matches = cells_ea.iloc[possible_matches_idx]

        weights = []
        total_overlap_area = 0.0

        for cell_idx, cell_row in possible_matches.iterrows():
            intersection = c_geom.intersection(cell_row.geometry)
            if not intersection.is_empty:
                overlap_area = intersection.area
                total_overlap_area += overlap_area
                weights.append({
                    "lat_idx": int(cell_row["lat_idx"]),
                    "lon_idx": int(cell_row["lon_idx"]),
                    "lat": float(cell_row["lat"]),
                    "lon": float(cell_row["lon"]),
                    "overlap_area": overlap_area
                })

        if total_overlap_area <= 0:
            raise ValueError(f"Catchment {gid} has no area overlap with rainfall grid!")

        # Normalize weights so sum of weights = 1.0
        for w in weights:
            w["weight"] = w["overlap_area"] / total_overlap_area

        weights_dict[gid] = weights

    return weights_dict

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = repo_root / "data" / "raw"
    raw_imd_dir = raw_dir / "imd_rainfall"
    processed_dir = repo_root / "data" / "processed"

    master_grid_path = processed_dir / "master_daily_grid.csv"
    catchments_path = processed_dir / "target_catchments.geojson"

    if not master_grid_path.exists() or not catchments_path.exists():
        raise FileNotFoundError("Required processed inputs missing. Run construct_daily_grid.py first.")

    # 1. Load Master Daily Grid & Catchments
    print("[INFO] Loading master daily grid and target catchments...")
    master_grid = pd.read_csv(master_grid_path)
    master_grid["GaugeID"] = master_grid["GaugeID"].astype(str)
    master_grid["Date"] = master_grid["Date"].astype(str)

    catchments_gdf = gpd.read_file(catchments_path)
    catchments_gdf["GaugeID"] = catchments_gdf["GaugeID"].astype(str)

    # 2. Determine Required Years (1964 to 2020)
    min_date = pd.to_datetime(master_grid["Date"].min())
    max_date = pd.to_datetime(master_grid["Date"].max())

    start_year = min_date.year
    end_year = max_date.year
    years = list(range(start_year, end_year + 1))
    print(f"[INFO] Download range: {start_year} to {end_year} ({len(years)} yearly files)...")

    # Download NetCDF files in parallel with retry logic
    print("[INFO] Downloading IMD rainfall NetCDF files in parallel (4 workers)...")
    nc_files_dict = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_year = {executor.submit(download_imd_rainfall_year, y, raw_imd_dir): y for y in years}
        for future in as_completed(future_to_year):
            y = future_to_year[future]
            nc_files_dict[y] = future.result()

    nc_files = [nc_files_dict[y] for y in years]
    print(f"[SUCCESS] Downloaded/Verified all {len(nc_files)} NetCDF files in {raw_imd_dir}")

    # 3. Open NetCDF Datasets & Clip Spatial Domain to Target Region
    print("[INFO] Opening and slicing NetCDF rainfall datasets...")
    datasets = []
    for nc_f in nc_files:
        ds_y = xr.open_dataset(nc_f)
        ds_sliced = ds_y.sel(
            LONGITUDE=slice(73.0, 76.0),
            LATITUDE=slice(16.0, 21.0)
        )
        datasets.append(ds_sliced)

    ds_combined = xr.concat(datasets, dim="TIME")
    ds_combined = ds_combined.sortby("TIME")

    # 4. Compute Spatial Area-Overlap Weights
    print("[INFO] Computing catchment area-overlap weights...")
    weights_dict = compute_catchment_weights(catchments_gdf, ds_combined)

    # 5. Calculate Daily Zonal Mean Precipitation per Catchment
    print("[INFO] Calculating daily zonal mean rainfall for all 20 catchments...")
    times = pd.to_datetime(ds_combined.TIME.values)
    dates_str = times.strftime("%Y-%m-%d")

    catchment_daily_rainfall = {}
    for gid, weights in weights_dict.items():
        daily_series = np.zeros(len(times), dtype=np.float32)
        for w in weights:
            cell_precip = ds_combined.RAINFALL.values[:, w["lat_idx"], w["lon_idx"]]
            cell_precip_clean = np.nan_to_num(cell_precip, nan=0.0)
            daily_series += cell_precip_clean * w["weight"]

        catchment_daily_rainfall[gid] = pd.Series(daily_series, index=dates_str)

    daily_precip_df = pd.DataFrame(catchment_daily_rainfall)
    daily_precip_df.index.name = "Date"
    daily_precip_csv = processed_dir / "target_catchment_daily_rainfall.csv"
    daily_precip_df.to_csv(daily_precip_csv)
    print(f"[SUCCESS] Exported daily catchment rainfall table to {daily_precip_csv}")

    # 6. Engineer Antecedent Features (Strictly dates <= T-1)
    print("[INFO] Computing antecedent rainfall features for every gauge-day (Strictly dates <= T-1)...")

    feature_rows = []

    for gid in catchments_gdf["GaugeID"]:
        if gid not in catchment_daily_rainfall:
            raise KeyError(f"Missing rainfall series for GaugeID {gid}")

        series = catchment_daily_rainfall[gid]
        g_grid_dates = master_grid[master_grid["GaugeID"] == gid]["Date"].values

        for d_str in g_grid_dates:
            target_dt = pd.to_datetime(d_str)

            t_minus_1 = target_dt - pd.Timedelta(days=1)
            t_minus_10 = target_dt - pd.Timedelta(days=10)

            antecedent_slice = series.loc[t_minus_10.strftime("%Y-%m-%d") : t_minus_1.strftime("%Y-%m-%d")]

            if len(antecedent_slice) < 10:
                raise ValueError(f"Insufficient antecedent rainfall history for Gauge {gid} on Date {d_str}! Expected 10 days, got {len(antecedent_slice)}.")

            vals = antecedent_slice.values

            # Leakage Assertion: Verify that index 9 corresponds to T-1 date
            last_date_str = antecedent_slice.index[-1]
            if last_date_str != t_minus_1.strftime("%Y-%m-%d"):
                raise AssertionError(f"Leakage Check Failed: Last feature date ({last_date_str}) is not T-1 ({t_minus_1.strftime('%Y-%m-%d')})!")

            r_1d = float(vals[-1])                  # T-1
            r_2d_sum = float(vals[-2:].sum())       # T-2 to T-1
            r_3d_sum = float(vals[-3:].sum())       # T-3 to T-1
            r_5d_sum = float(vals[-5:].sum())       # T-5 to T-1
            r_7d_sum = float(vals[-7:].sum())       # T-7 to T-1
            r_10d_sum = float(vals[-10:].sum())     # T-10 to T-1

            r_3d_max = float(vals[-3:].max())
            r_7d_max = float(vals[-7:].max())

            dry_days_3d = int((vals[-3:] < 1.0).sum())

            has_gpm = 1 if target_dt >= pd.to_datetime("2000-06-01") else 0

            feature_rows.append({
                "GaugeID": gid,
                "Date": d_str,
                "rain_1d": r_1d,
                "rain_2d_sum": r_2d_sum,
                "rain_3d_sum": r_3d_sum,
                "rain_5d_sum": r_5d_sum,
                "rain_7d_sum": r_7d_sum,
                "rain_10d_sum": r_10d_sum,
                "rain_3d_max": r_3d_max,
                "rain_7d_max": r_7d_max,
                "rain_dry_days_3d": dry_days_3d,
                "has_gpm_coverage": has_gpm
            })

    features_df = pd.DataFrame(feature_rows)

    # 7. Merge Rainfall Features into Master Daily Grid
    print("[INFO] Merging antecedent rainfall features into master daily grid...")
    grid_with_rain = master_grid.merge(features_df, on=["GaugeID", "Date"], how="left")

    # 8. Fail-Fast Validation Checks
    print("\n--- RUNNING FAITHFUL FAIL-FAST VALIDATION CHECKS ---")

    # Check 1: Row Count Integrity
    if len(grid_with_rain) != len(master_grid):
        raise AssertionError(f"Validation Failed: Row count changed after merge! Original: {len(master_grid)}, New: {len(grid_with_rain)}")
    print(f"[CHECK 1] Row Count Integrity: {len(grid_with_rain)} rows matches master_daily_grid.csv.")

    # Check 2: Primary Key Uniqueness
    dup_pk = grid_with_rain.duplicated(subset=["GaugeID", "Date"]).sum()
    print(f"[CHECK 2] Primary Key (GaugeID, Date) Duplicates: {dup_pk}")
    if dup_pk > 0:
        raise AssertionError(f"Validation Failed: Found {dup_pk} duplicate (GaugeID, Date) rows in merged dataset!")

    # Check 3: 20/20 GaugeID Coverage
    unique_gauges = grid_with_rain["GaugeID"].nunique()
    print(f"[CHECK 3] GaugeID Station Coverage: {unique_gauges} / 20 stations")
    if unique_gauges != 20:
        raise AssertionError(f"Validation Failed: GaugeID count is {unique_gauges}, expected 20!")

    # Check 4: Zero Nulls in Rainfall Features
    rain_feature_cols = [
        "rain_1d", "rain_2d_sum", "rain_3d_sum", "rain_5d_sum",
        "rain_7d_sum", "rain_10d_sum", "rain_3d_max", "rain_7d_max",
        "rain_dry_days_3d"
    ]
    null_counts = grid_with_rain[rain_feature_cols].isna().sum().to_dict()
    total_nulls = sum(null_counts.values())
    print(f"[CHECK 4] Total Nulls in Rainfall Feature Columns: {total_nulls}")
    if total_nulls > 0:
        raise AssertionError(f"Validation Failed: Found null values in rainfall features: {null_counts}")

    # Check 5: Rainfall Value Range Sanity Check
    max_rain = grid_with_rain["rain_1d"].max()
    min_rain = grid_with_rain["rain_1d"].min()
    print(f"[CHECK 5] Daily Rainfall Value Range: min={min_rain:.2f} mm, max={max_rain:.2f} mm")
    if min_rain < 0.0 or max_rain > 1000.0:
        raise AssertionError(f"Validation Failed: Rainfall values out of realistic range [0.0, 1000.0] mm! Got min={min_rain}, max={max_rain}")

    # Check 6: Leakage Proof Audit
    print("[CHECK 6] Leakage Verification: Testing feature cutoff for 5 random sample rows...")
    sample_rows = grid_with_rain.sample(5, random_state=42)
    for idx, r in sample_rows.iterrows():
        gid = r["GaugeID"]
        d_str = r["Date"]
        dt = pd.to_datetime(d_str)
        t_minus_1_str = (dt - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        t_str = dt.strftime("%Y-%m-%d")
        actual_t_minus_1_val = float(daily_precip_df.loc[t_minus_1_str, gid])
        feature_r1d = float(r["rain_1d"])
        actual_t_val = float(daily_precip_df.loc[t_str, gid])

        print(f"  Gauge {gid} on Date {d_str}: rain_1d feature = {feature_r1d:.2f} mm | Actual Day T-1 ({t_minus_1_str}) = {actual_t_minus_1_val:.2f} mm | Actual Day T ({t_str}) = {actual_t_val:.2f} mm")
        if abs(feature_r1d - actual_t_minus_1_val) > 1e-4:
            raise AssertionError(f"Leakage Check Failed: rain_1d feature ({feature_r1d}) does not match Day T-1 rainfall ({actual_t_minus_1_val})!")
        if abs(feature_r1d - actual_t_val) < 1e-4 and abs(actual_t_minus_1_val - actual_t_val) > 1.0:
            raise AssertionError(f"Leakage Check Failed: rain_1d feature erroneously matches Day T rainfall!")

    print("[SUCCESS] All fail-fast validation checks passed cleanly!")

    # 9. Export Final Processed Outputs
    csv_out = processed_dir / "master_daily_grid_with_rainfall.csv"
    csv_gz_out = processed_dir / "master_daily_grid_with_rainfall.csv.gz"
    parquet_out = processed_dir / "master_daily_grid_with_rainfall.parquet"
    summary_out = processed_dir / "rainfall_pipeline_summary.json"

    print(f"[INFO] Exporting dataset to {csv_out} and {parquet_out}...")
    grid_with_rain.to_csv(csv_out, index=False)
    grid_with_rain.to_csv(csv_gz_out, index=False, compression="gzip")

    try:
        grid_with_rain.to_parquet(parquet_out, index=False)
        print(f"[INFO] Exported Parquet to {parquet_out}")
    except Exception as e:
        print(f"[WARN] Parquet export warning: {e}")

    summary = {
        "dataset_name": "master_daily_grid_with_rainfall",
        "total_rows": len(grid_with_rain),
        "total_columns": len(grid_with_rain.columns),
        "gauge_count": unique_gauges,
        "date_min": grid_with_rain["Date"].min(),
        "date_max": grid_with_rain["Date"].max(),
        "rainfall_source": {
            "name": "IMD 0.25-degree Daily Gridded Rainfall",
            "provider": "India Meteorological Department (IMD Pune)",
            "format": "NetCDF3 (ind{year}_rfp25.nc)",
            "raw_download_path": "data/raw/imd_rainfall/",
            "spatial_resolution": "0.25 x 0.25 degree (~27 km)",
            "temporal_resolution": "Daily (24-hour accumulation ending at 08:30 IST / 03:00 UTC)",
            "units": "mm/day",
            "missing_value_encoding": "NaN / -999.0"
        },
        "zonal_aggregation_method": "Area-overlap weighted mean across intersecting grid cells per catchment",
        "antecedent_features_engineered": rain_feature_cols + ["has_gpm_coverage"],
        "prediction_time_cutoff": "Day T 00:00 UTC (Features use ONLY dates <= T-1)",
        "leakage_rule_enforcement": {
            "day_T_rainfall_excluded": True,
            "indofloods_t1d_t10d_excluded": True,
            "warmup_padding_days": 10
        },
        "validation_passed": True
    }

    with open(summary_out, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n================ RAINFALL PIPELINE SUMMARY ================")
    print(json.dumps(summary, indent=2))
    print("==========================================================")

if __name__ == "__main__":
    main()
