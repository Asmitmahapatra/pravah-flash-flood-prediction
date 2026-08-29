"""
filter_target_region.py

Filters INDOFLOODS raw tables and cleaned catchment geometries to the verified 20
Maharashtra Western Ghats study-region catchments.

Preserves relational integrity using GaugeID as the primary key.
Exports filtered datasets and a validation summary to data/processed/.
"""

from pathlib import Path
import json
import re
import pandas as pd
import geopandas as gpd

TARGET_GAUGE_IDS = [
    "585", "589", "596", "602", "612", "626", "635", "640", "642", "643",
    "645", "646", "648", "654", "656", "668", "678", "681", "682", "684"
]

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
    raw_dir = repo_root / "data" / "raw" / "indofloods"
    processed_dir = repo_root / "data" / "processed"
    clean_geojson_path = processed_dir / "clean_catchments.geojson"

    if not clean_geojson_path.exists():
        raise FileNotFoundError(f"Cleaned catchments file not found at {clean_geojson_path}. Run clean_catchment_geometries.py first.")

    # 1. Load Datasets
    print("[INFO] Loading raw INDOFLOODS datasets and cleaned catchments GeoJSON...")
    catchments_gdf = gpd.read_file(clean_geojson_path)
    metadata_df = pd.read_csv(raw_dir / "metadata_indofloods.csv")
    events_df = pd.read_csv(raw_dir / "floodevents_indofloods.csv")
    characteristics_df = pd.read_csv(raw_dir / "catchment_characteristics_indofloods.csv")
    precip_df = pd.read_csv(raw_dir / "precipitation_variables_indofloods.csv")

    # Record counts before
    counts_before = {
        "catchments_geojson_features": len(catchments_gdf),
        "metadata_rows": len(metadata_df),
        "floodevents_rows": len(events_df),
        "catchment_characteristics_rows": len(characteristics_df),
        "precipitation_variables_rows": len(precip_df)
    }

    # Normalize GaugeID across all datasets
    catchments_gdf["clean_GaugeID"] = catchments_gdf["GaugeID"].apply(extract_clean_gauge_id)
    metadata_df["clean_GaugeID"] = metadata_df["GaugeID"].apply(extract_clean_gauge_id)
    characteristics_df["clean_GaugeID"] = characteristics_df["GaugeID"].apply(extract_clean_gauge_id)

    events_df["clean_GaugeID"] = events_df["EventID"].apply(extract_clean_gauge_id)
    precip_df["clean_GaugeID"] = precip_df["EventID"].apply(extract_clean_gauge_id)

    # 2. Filter Datasets to TARGET_GAUGE_IDS
    print(f"[INFO] Filtering to {len(TARGET_GAUGE_IDS)} Maharashtra Western Ghats target GaugeIDs...")

    target_set = set(TARGET_GAUGE_IDS)

    target_catchments_gdf = catchments_gdf[catchments_gdf["clean_GaugeID"].isin(target_set)].copy()
    target_metadata_df = metadata_df[metadata_df["clean_GaugeID"].isin(target_set)].copy()
    target_characteristics_df = characteristics_df[characteristics_df["clean_GaugeID"].isin(target_set)].copy()
    target_events_df = events_df[events_df["clean_GaugeID"].isin(target_set)].copy()

    target_event_ids = set(target_events_df["EventID"])
    target_precip_df = precip_df[precip_df["EventID"].isin(target_event_ids)].copy()

    # Drop temporary helper column
    target_catchments_gdf = target_catchments_gdf.drop(columns=["clean_GaugeID"])
    target_metadata_df = target_metadata_df.drop(columns=["clean_GaugeID"])
    target_characteristics_df = target_characteristics_df.drop(columns=["clean_GaugeID"])
    target_events_df = target_events_df.drop(columns=["clean_GaugeID"])
    target_precip_df = target_precip_df.drop(columns=["clean_GaugeID"])

    # Record counts after
    counts_after = {
        "catchments_geojson_features": len(target_catchments_gdf),
        "metadata_rows": len(target_metadata_df),
        "floodevents_rows": len(target_events_df),
        "catchment_characteristics_rows": len(target_characteristics_df),
        "precipitation_variables_rows": len(target_precip_df)
    }

    # 3. Validation & Relational Integrity Checks
    catchment_gids = set(target_catchments_gdf["GaugeID"].apply(extract_clean_gauge_id))
    metadata_gids = set(target_metadata_df["GaugeID"].apply(extract_clean_gauge_id))
    characteristics_gids = set(target_characteristics_df["GaugeID"].apply(extract_clean_gauge_id))
    events_gids = set(target_events_df["EventID"].apply(extract_clean_gauge_id))

    missing_in_catchments = sorted(list(target_set - catchment_gids))
    missing_in_metadata = sorted(list(target_set - metadata_gids))
    missing_in_characteristics = sorted(list(target_set - characteristics_gids))
    missing_in_events = sorted(list(target_set - events_gids))

    # Orphan checks
    orphan_events = target_events_df[~target_events_df["EventID"].apply(extract_clean_gauge_id).isin(target_set)]
    orphan_precip = target_precip_df[~target_precip_df["EventID"].isin(target_event_ids)]

    # Geometry checks
    invalid_geoms = (~target_catchments_gdf.is_valid).sum()
    crs_str = target_catchments_gdf.crs.to_string() if target_catchments_gdf.crs else "None"

    # Per-gauge event counts and flood severity breakdown
    gauge_event_summary = {}
    for gid in sorted(TARGET_GAUGE_IDS, key=int):
        g_events = target_events_df[target_events_df["EventID"].apply(extract_clean_gauge_id) == gid]
        flood_types = g_events["Flood Type"].value_counts().to_dict()
        gauge_event_summary[gid] = {
            "total_events": len(g_events),
            "flood_types": {str(k): int(v) for k, v in flood_types.items()}
        }

    # 4. Save Filtered Output Files
    print("[INFO] Saving filtered outputs to data/processed/...")
    target_catchments_gdf.to_file(processed_dir / "target_catchments.geojson", driver="GeoJSON")
    target_metadata_df.to_csv(processed_dir / "target_metadata.csv", index=False)
    target_events_df.to_csv(processed_dir / "target_floodevents.csv", index=False)
    target_characteristics_df.to_csv(processed_dir / "target_catchment_characteristics.csv", index=False)
    target_precip_df.to_csv(processed_dir / "target_precipitation_variables.csv", index=False)

    summary = {
        "target_region": "Maharashtra Western Ghats 100km Crest Corridor Proxy",
        "target_gauge_ids": TARGET_GAUGE_IDS,
        "target_gauge_count": len(TARGET_GAUGE_IDS),
        "counts_before": counts_before,
        "counts_after": counts_after,
        "missing_records": {
            "missing_in_catchments_vector": missing_in_catchments,
            "missing_in_metadata": missing_in_metadata,
            "missing_in_characteristics": missing_in_characteristics,
            "missing_in_events": missing_in_events
        },
        "orphan_records": {
            "orphan_floodevents": len(orphan_events),
            "orphan_precipitation_rows": len(orphan_precip)
        },
        "geospatial_validation": {
            "crs": crs_str,
            "invalid_geometries_count": int(invalid_geoms),
            "geometry_types": {str(k): int(v) for k, v in target_catchments_gdf.geometry.type.value_counts().to_dict().items()}
        },
        "per_gauge_event_summary": gauge_event_summary
    }

    with open(processed_dir / "target_region_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n================ VALIDATION SUMMARY ================")
    print(json.dumps(summary, indent=2))
    print("====================================================")
    print(f"[SUCCESS] Filtered datasets exported to {processed_dir}")

if __name__ == "__main__":
    main()
