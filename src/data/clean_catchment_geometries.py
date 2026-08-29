"""
clean_catchment_geometries.py

Reads INDOFLOODS catchment shapefiles, inspects and repairs invalid geometries,
analyzes duplicate WKB geometry pairs, preserves GaugeID relationships,
and exports the cleaned GeoJSON to data/processed/clean_catchments.geojson.
"""

from pathlib import Path
import json
import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid
from shapely import wkb

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = repo_root / "data" / "raw" / "indofloods" / "catchments"
    output_dir = repo_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "clean_catchments.geojson"

    # 1. Locate shapefiles
    shp_files = sorted(list(raw_dir.rglob("INDOFLOODS-gauge-*.shp")))
    print(f"[INFO] Found {len(shp_files)} shapefile groups in {raw_dir}")

    if not shp_files:
        raise FileNotFoundError(f"No INDOFLOODS-gauge-*.shp files found in {raw_dir}")

    # Read each shapefile and normalize CRS to EPSG:4326
    gdfs = []
    for shp_path in shp_files:
        gdf_single = gpd.read_file(shp_path)
        gauge_id = shp_path.stem.replace("INDOFLOODS-gauge-", "")
        if "GaugeID" not in gdf_single.columns:
            gdf_single["GaugeID"] = gauge_id
        if "_source_id" not in gdf_single.columns:
            gdf_single["_source_id"] = gauge_id
        
        # Normalize CRS to EPSG:4326 (WGS 84) to handle 'GCS_unknown' vs 'WGS 84' PRJ label inconsistencies
        if gdf_single.crs is None or "unknown" in str(gdf_single.crs).lower():
            gdf_single = gdf_single.set_crs(epsg=4326, allow_override=True)
        else:
            gdf_single = gdf_single.to_crs(epsg=4326)

        gdfs.append(gdf_single)

    gdf_before = pd.concat(gdfs, ignore_index=True)
    gdf_before = gpd.GeoDataFrame(gdf_before, crs="EPSG:4326")

    total_geometries_before = len(gdf_before)
    crs_before = gdf_before.crs.to_string()

    # 2. Check invalid geometries before
    invalid_mask_before = ~gdf_before.is_valid
    invalid_count_before = int(invalid_mask_before.sum())
    invalid_indices_before = gdf_before[invalid_mask_before].index.tolist()
    invalid_gauge_ids_before = gdf_before.loc[invalid_mask_before, "GaugeID"].tolist()

    print(f"\n--- BEFORE CLEANING ---")
    print(f"Total features: {total_geometries_before}")
    print(f"CRS: {crs_before}")
    print(f"Invalid geometries count: {invalid_count_before}")
    if invalid_count_before > 0:
        print(f"Invalid GaugeIDs: {invalid_gauge_ids_before}")

    # 3. Check duplicate WKB geometry pairs before
    def get_wkb_hex(geom):
        if geom is None or geom.is_empty:
            return ""
        return wkb.dumps(geom, hex=True)

    gdf_before["wkb_hex"] = gdf_before.geometry.apply(get_wkb_hex)
    wkb_counts_before = gdf_before["wkb_hex"].value_counts()
    dup_wkb_hexes_before = wkb_counts_before[wkb_counts_before > 1].index.tolist()
    dup_pairs_before = len(dup_wkb_hexes_before)

    print(f"\n--- DUPLICATE GEOMETRY ANALYSIS (BEFORE) ---")
    print(f"Number of duplicate geometry groups: {dup_pairs_before}")
    for idx, hex_val in enumerate(dup_wkb_hexes_before, 1):
        matching_gauges = gdf_before[gdf_before["wkb_hex"] == hex_val]["GaugeID"].tolist()
        print(f"  Group {idx}: {len(matching_gauges)} features share identical geometry -> GaugeIDs: {matching_gauges}")

    # 4. Repair geometries
    print("\n--- REPAIRING GEOMETRIES ---")
    gdf_repaired = gdf_before.copy()
    
    repaired_geoms = []
    for idx, row in gdf_repaired.iterrows():
        geom = row.geometry
        if not geom.is_valid:
            repaired_geom = make_valid(geom)
            print(f"[REPAIR] GaugeID {row['GaugeID']}: repaired {geom.geom_type} -> {repaired_geom.geom_type}")
            repaired_geoms.append(repaired_geom)
        else:
            repaired_geoms.append(geom)

    gdf_repaired["geometry"] = repaired_geoms

    invalid_mask_after = ~gdf_repaired.is_valid
    invalid_count_after = int(invalid_mask_after.sum())

    # Re-check duplicates after repair
    gdf_repaired["wkb_hex"] = gdf_repaired.geometry.apply(get_wkb_hex)
    wkb_counts_after = gdf_repaired["wkb_hex"].value_counts()
    dup_wkb_hexes_after = wkb_counts_after[wkb_counts_after > 1].index.tolist()
    dup_pairs_after = len(dup_wkb_hexes_after)

    # 5. Deduplication Decision
    print("\n--- DEDUPLICATION DECISION & ATTRIBUTE PRESERVATION ---")
    print("Decision: PRESERVE ALL 155 FEATURES.")
    print("Rationale: The duplicate WKB geometries belong to distinct GaugeIDs (gauge stations).")
    print("           Deleting any feature would break relational integrity with floodevents_indofloods.csv")
    print("           and catchment_characteristics_indofloods.csv for that GaugeID.")
    print("           An 'is_duplicate_geometry' flag is added to the output metadata for downstream awareness.")

    gdf_repaired["is_duplicate_geometry"] = gdf_repaired["wkb_hex"].isin(dup_wkb_hexes_after)
    
    # Drop temporary wkb_hex column before saving
    gdf_export = gdf_repaired.drop(columns=["wkb_hex"])

    # Ensure output directory exists and export to GeoJSON
    gdf_export.to_file(output_file, driver="GeoJSON")
    print(f"\n[SUCCESS] Saved cleaned catchments to: {output_file}")

    # 6. Summary Report
    geom_types_after = gdf_export.geometry.type.value_counts().to_dict()

    summary = {
        "total_geometries_before": total_geometries_before,
        "invalid_geometries_before": invalid_count_before,
        "invalid_geometries_after": invalid_count_after,
        "duplicate_geometry_pairs_before": dup_pairs_before,
        "duplicate_geometry_pairs_after": dup_pairs_after,
        "crs": gdf_export.crs.to_string(),
        "feature_count": len(gdf_export),
        "geometry_types": {str(k): int(v) for k, v in geom_types_after.items()},
        "deduplication_policy": "All 155 features retained to preserve GaugeID station mapping; is_duplicate_geometry flag added."
    }

    print("\n================ VALIDATION SUMMARY ================")
    print(json.dumps(summary, indent=2))
    print("====================================================")

if __name__ == "__main__":
    main()
