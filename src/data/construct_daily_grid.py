"""
construct_daily_grid.py

Constructs the master Date x GaugeID daily spatio-temporal grid for the 20 target
Maharashtra Western Ghats catchments.

Maps INDOFLOODS flood events to daily target labels (target_onset, target_active, target_peak)
with explicit precedence resolution for overlaps.

Calculates all expected counts dynamically from source data and fails validation
if any count or constraint mismatches.
"""

from pathlib import Path
import json
import re
import pandas as pd
import geopandas as gpd

def extract_clean_gauge_id(val) -> str:
    """Standardizes GaugeID to clean numeric string (e.g., 'INDOFLOODS-gauge-643-1' -> '643')."""
    val_str = str(val)
    match = re.search(r"INDOFLOODS-gauge-(\d+)", val_str)
    if match:
        return match.group(1)
    match_num = re.search(r"^(\d+)$", val_str)
    if match_num:
        return match_num.group(1)
    return val_str

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    processed_dir = repo_root / "data" / "processed"

    metadata_path = processed_dir / "target_metadata.csv"
    events_path = processed_dir / "target_floodevents.csv"
    characteristics_path = processed_dir / "target_catchment_characteristics.csv"
    catchments_path = processed_dir / "target_catchments.geojson"

    for p in [metadata_path, events_path, characteristics_path, catchments_path]:
        if not p.exists():
            raise FileNotFoundError(f"Required target dataset not found: {p}. Run filter_target_region.py first.")

    # 1. Load Filtered Target Data
    print("[INFO] Loading target region datasets...")
    metadata_df = pd.read_csv(metadata_path)
    events_df = pd.read_csv(events_path)
    characteristics_df = pd.read_csv(characteristics_path)
    catchments_gdf = gpd.read_file(catchments_path)

    metadata_df["clean_GaugeID"] = metadata_df["GaugeID"].apply(extract_clean_gauge_id)
    characteristics_df["clean_GaugeID"] = characteristics_df["GaugeID"].apply(extract_clean_gauge_id)
    events_df["clean_GaugeID"] = events_df["EventID"].apply(extract_clean_gauge_id)
    catchments_gdf["clean_GaugeID"] = catchments_gdf["GaugeID"].apply(extract_clean_gauge_id)

    # 2. Dynamic Source Calculation for Expected Observation Grid
    print("[INFO] Calculating expected observation grid bounds dynamically from metadata...")
    expected_gauge_days_dict = {}
    total_expected_grid_rows = 0

    grid_dfs = []
    for idx, row in metadata_df.iterrows():
        gid = row["clean_GaugeID"]
        s_date = pd.to_datetime(row["Start_date"])
        e_date = pd.to_datetime(row["End_date"])

        if pd.isna(s_date) or pd.isna(e_date):
            raise ValueError(f"Gauge {gid} has invalid metadata Start_date or End_date!")

        date_range = pd.date_range(start=s_date, end=e_date, freq="D")
        num_days = len(date_range)
        expected_gauge_days_dict[gid] = num_days
        total_expected_grid_rows += num_days

        station_grid = pd.DataFrame({
            "GaugeID": gid,
            "Date": date_range.strftime("%Y-%m-%d")
        })
        grid_dfs.append(station_grid)

    master_grid = pd.concat(grid_dfs, ignore_index=True)

    print(f"[INFO] Generated master grid with {len(master_grid)} rows across {len(expected_gauge_days_dict)} stations.")
    if len(master_grid) != total_expected_grid_rows:
        raise AssertionError(f"Master grid row count ({len(master_grid)}) does not match calculated total ({total_expected_grid_rows})!")

    # 3. Dynamic Calculation of Event Assignments & Overlap Detection
    print("[INFO] Processing event mappings and checking for active event-day overlaps...")

    def get_type_code(ftype: str) -> int:
        ftype_str = str(ftype).strip().lower()
        if "severe" in ftype_str:
            return 2
        elif "flood" in ftype_str:
            return 1
        return 0

    events_df["type_code"] = events_df["Flood Type"].apply(get_type_code)

    onset_dict = {}     # (GaugeID, Date) -> max type_code
    peak_dict = {}      # (GaugeID, Date) -> max type_code
    active_assignments = []

    total_event_day_assignments = 0

    for idx, row in events_df.iterrows():
        gid = row["clean_GaugeID"]
        s_date_str = str(row["Start Date"]).strip()
        e_date_str = str(row["End Date"]).strip()
        peak_date_str = str(row["Peak FL Date"]).strip() if pd.notna(row["Peak FL Date"]) else None
        type_code = row["type_code"]
        event_id = row["EventID"]

        s_date = pd.to_datetime(s_date_str)
        e_date = pd.to_datetime(e_date_str)
        duration_days = (e_date - s_date).days + 1
        total_event_day_assignments += duration_days

        # Onset
        key_onset = (gid, s_date_str)
        onset_dict[key_onset] = max(onset_dict.get(key_onset, 0), type_code)

        # Peak
        if peak_date_str and peak_date_str != "nan":
            key_peak = (gid, peak_date_str)
            peak_dict[key_peak] = max(peak_dict.get(key_peak, 0), type_code)

        # Active days
        active_range = pd.date_range(start=s_date, end=e_date, freq="D")
        for d in active_range:
            d_str = d.strftime("%Y-%m-%d")
            active_assignments.append({
                "GaugeID": gid,
                "Date": d_str,
                "type_code": type_code,
                "EventID": event_id
            })

    active_df = pd.DataFrame(active_assignments)

    # Detect overlaps
    overlap_groups = active_df.groupby(["GaugeID", "Date"])
    overlap_collisions = []
    active_dict = {}

    for (gid, d_str), group in overlap_groups:
        max_code = group["type_code"].max()
        active_dict[(gid, d_str)] = max_code

        if len(group) > 1:
            overlap_collisions.append({
                "GaugeID": gid,
                "Date": d_str,
                "event_count": len(group),
                "event_ids": group["EventID"].tolist(),
                "type_codes": group["type_code"].tolist(),
                "resolved_type_code": max_code
            })

    unique_active_gauge_days = len(active_dict)

    print(f"[INFO] Event Summary:")
    print(f"  Total event records: {len(events_df)}")
    print(f"  Total event-day assignments: {total_event_day_assignments}")
    print(f"  Unique active gauge-days: {unique_active_gauge_days}")
    print(f"  Overlapping gauge-day collisions detected & resolved: {len(overlap_collisions)}")

    # 4. Map Target Labels to Master Grid
    print("[INFO] Mapping target labels into master daily grid...")
    master_grid["target_onset"] = master_grid.apply(lambda r: onset_dict.get((r["GaugeID"], r["Date"]), 0), axis=1)
    master_grid["target_active"] = master_grid.apply(lambda r: active_dict.get((r["GaugeID"], r["Date"]), 0), axis=1)
    master_grid["target_peak"] = master_grid.apply(lambda r: peak_dict.get((r["GaugeID"], r["Date"]), 0), axis=1)

    # 5. Join Metadata & Static Characteristics
    print("[INFO] Joining station metadata and static catchment characteristics...")

    meta_copy = metadata_df.copy()
    meta_copy["GaugeID"] = meta_copy["clean_GaugeID"]
    meta_sub = meta_copy[[
        "GaugeID", "Station", "Latitude", "Longitude",
        "River Name/ Tributory/ SubTributory", "Basin", "State",
        "Warning Level", "Danger Level", "Privacy"
    ]].rename(columns={
        "River Name/ Tributory/ SubTributory": "River_Name",
        "Warning Level": "Warning_Level",
        "Danger Level": "Danger_Level"
    })

    char_copy = characteristics_df.copy()
    char_copy["GaugeID"] = char_copy["clean_GaugeID"]
    char_sub = char_copy.drop(columns=["clean_GaugeID"])

    master_grid = master_grid.merge(meta_sub, on="GaugeID", how="left")
    master_grid = master_grid.merge(char_sub, on="GaugeID", how="left")

    # 6. Empirical Validation Checks (Fail-Fast Verification)
    print("\n--- RUNNING FAITHFUL EMPIRICAL VALIDATION CHECKS ---")

    # Check 1: Primary Key Uniqueness
    dup_pk_count = master_grid.duplicated(subset=["GaugeID", "Date"]).sum()
    print(f"[CHECK 1] Primary Key (GaugeID, Date) Duplicates: {dup_pk_count}")
    if dup_pk_count > 0:
        raise AssertionError(f"Validation Failed: Found {dup_pk_count} duplicate (GaugeID, Date) rows in master grid!")

    # Check 2: Total Grid Rows vs Metadata Observation Bounds
    if len(master_grid) != total_expected_grid_rows:
        raise AssertionError(f"Validation Failed: Master grid row count ({len(master_grid)}) does not match dynamically calculated expected total ({total_expected_grid_rows})!")
    print(f"[CHECK 2] Master Grid Row Count: {len(master_grid)} matches expected calculated bounds.")

    # Check 3: Target Onset Positive Counts
    onset_positives = (master_grid["target_onset"] > 0).sum()
    print(f"[CHECK 3] Target Onset Positive Days: {onset_positives} (Expected: {len(onset_dict)})")
    if onset_positives != len(onset_dict):
        raise AssertionError(f"Validation Failed: Onset positive count ({onset_positives}) differs from unique onset dates ({len(onset_dict)})!")

    # Check 4: Target Active Positive Counts vs Unique Active Days
    active_positives = (master_grid["target_active"] > 0).sum()
    print(f"[CHECK 4] Target Active Positive Days: {active_positives} (Expected Unique Active Gauge-Days: {unique_active_gauge_days})")
    if active_positives != unique_active_gauge_days:
        raise AssertionError(f"Validation Failed: Active positive count ({active_positives}) differs from unique active days ({unique_active_gauge_days})!")

    # Check 5: Target Peak Positive Counts
    peak_positives = (master_grid["target_peak"] > 0).sum()
    print(f"[CHECK 5] Target Peak Positive Days: {peak_positives} (Expected: {len(peak_dict)})")
    if peak_positives != len(peak_dict):
        raise AssertionError(f"Validation Failed: Peak positive count ({peak_positives}) differs from unique peak dates ({len(peak_dict)})!")

    # Check 6: Orphan Check (Ensure all 286 event IDs mapped)
    all_mapped_onset_keys = set(onset_dict.keys())
    grid_keys = set(zip(master_grid["GaugeID"], master_grid["Date"]))
    unmapped_onsets = all_mapped_onset_keys - grid_keys
    print(f"[CHECK 6] Unmapped / Orphan Event Onsets: {len(unmapped_onsets)}")
    if unmapped_onsets:
        raise AssertionError(f"Validation Failed: Found {len(unmapped_onsets)} orphan event onsets outside metadata observation windows: {unmapped_onsets}")

    # Check 7: Leakage Exclusion Audit
    prohibited_post_event_cols = [
        "Peak Flood Level (m)", "Peak FL Date", "Peak Discharge Q (cumec)",
        "Peak Discharge Date", "Flood Volume (cumec)", "Event Duration (days)",
        "Time to Peak (days)", "Recession Time (day)"
    ]
    detected_leakage_cols = [c for c in prohibited_post_event_cols if c in master_grid.columns]
    print(f"[CHECK 7] Prohibited Post-Event Leakage Columns in Grid: {detected_leakage_cols}")
    if detected_leakage_cols:
        raise AssertionError(f"Validation Failed: Prohibited post-event leakage columns found in grid: {detected_leakage_cols}")

    # Check 8: Event-only Rainfall (T1d-T10d) Exclusion Audit
    t_cols = [f"T{i}d" for i in range(1, 11)]
    detected_t_cols = [c for c in t_cols if c in master_grid.columns]
    print(f"[CHECK 8] Event-Only T1d-T10d Rainfall Columns in Grid Predictors: {detected_t_cols}")
    if detected_t_cols:
        raise AssertionError(f"Validation Failed: Event-only T1d-T10d columns found in grid predictors: {detected_t_cols}")

    # 7. Export Master Grid & Machine-Readable Summary
    parquet_out = processed_dir / "master_daily_grid.parquet"
    csv_out = processed_dir / "master_daily_grid.csv"
    csv_gz_out = processed_dir / "master_daily_grid.csv.gz"
    summary_out = processed_dir / "daily_grid_summary.json"

    print(f"\n[INFO] Saving master daily grid to {csv_out} and {csv_gz_out}...")
    master_grid.to_csv(csv_out, index=False)
    master_grid.to_csv(csv_gz_out, index=False, compression="gzip")

    try:
        master_grid.to_parquet(parquet_out, index=False)
        print(f"[INFO] Saved Parquet to {parquet_out}")
    except Exception as e:
        print(f"[WARN] Could not save Parquet format ({e}). CSV and CSV.GZ exported successfully.")

    summary = {
        "master_grid_rows": len(master_grid),
        "target_stations_count": len(metadata_df),
        "total_expected_gauge_days": total_expected_grid_rows,
        "date_range_min": master_grid["Date"].min(),
        "date_range_max": master_grid["Date"].max(),
        "event_totals": {
            "total_event_records": len(events_df),
            "total_event_day_assignments": total_event_day_assignments,
            "unique_active_gauge_days": unique_active_gauge_days,
            "overlap_collisions_count": len(overlap_collisions)
        },
        "target_label_counts": {
            "target_onset": {str(k): int(v) for k, v in master_grid["target_onset"].value_counts().to_dict().items()},
            "target_active": {str(k): int(v) for k, v in master_grid["target_active"].value_counts().to_dict().items()},
            "target_peak": {str(k): int(v) for k, v in master_grid["target_peak"].value_counts().to_dict().items()}
        },
        "leakage_rules": {
            "post_event_variables_excluded": prohibited_post_event_cols,
            "t1d_t10d_rainfall_excluded": True,
            "precedence_rule_for_overlaps": "Severe Flood [2] > Flood [1] > No Event [0]"
        },
        "validation_passed": True
    }

    with open(summary_out, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n================ DAILY GRID VALIDATION SUMMARY ================")
    print(json.dumps(summary, indent=2))
    print("==============================================================")

if __name__ == "__main__":
    main()
