# INDOFLOODS Catchment Geospatial Quality Report

**Inspection date:** 2026-08-28  
**Input:** `data/raw/indofloods/catchments/` extracted from `catchments_shapefiles_indofloods.zip`.  
**Tooling:** GeoPandas 1.1.4, Pyogrio, Shapely 2.1.2, PyProj 3.7.2.

## Results

| Check | Result |
|---|---:|
| Shapefile groups inspected | 155 |
| Geometry features | 155 |
| Invalid geometries | 3 |
| Empty geometries | 0 |
| Exact duplicate geometries | 5 duplicate rows; 150 unique WKB geometries |
| Unique GaugeID/source IDs | 155 |
| Total geographic bounds | West 72.695, South 8.175, East 91.975, North 28.250 |
| Minimum catchment area | 34,026,074 m2, approximately 34.03 km2 |
| Maximum catchment area | 308,209,249,622 m2, approximately 308,209.25 km2 |
| Common normalized CRS | EPSG:4326 / WGS 84 |

Areas were calculated after normalizing the layers to WGS 84 and projecting to EPSG:6933. The source PRJ files are inconsistent in naming: most say `GCS_unknown` but specify the WGS 1984 datum, while some say `GCS_WGS_1984`. This is a naming inconsistency, not evidence of different geographic datums, but it must be normalized and recorded.

## GaugeID Matching

Each shapefile group is named `INDOFLOODS-gauge-{id}`. The 155 extracted source IDs are unique and match the 155 unique `GaugeID` values in `catchment_characteristics_indofloods.csv` after normalizing the common prefix. The catchment source IDs also match the corresponding gauge IDs in the INDOFLOODS metadata/event key scheme for the available 155 catchments.

The 214-station metadata table is larger than the 155-catchment geometry table. Therefore, a station having metadata or events does not imply that it has a supplied catchment polygon.

## Geometry Defects

- Three geometries are invalid and must be repaired or excluded after inspecting the specific features and repair effect.
- Five rows are exact duplicate geometries based on WKB equality. These may represent genuinely identical catchment polygons attached to different gauge IDs, duplicated source geometry, or a source construction issue. They must not be silently deduplicated because the gauge/event relationship could be meaningful.
- No geometry is empty.
- A GIS validity/repair audit of the three invalid features and a semantic review of the five duplicate geometry groups are required before spatial aggregation.

## Western Ghats Screening Proxy

No authoritative machine-readable Western Ghats boundary was obtained in this step. To avoid calling an entire state the Western Ghats, the initial screening used a clearly documented **physiographic proxy**: a 100 km corridor around an approximate Western Ghats crestline represented by a manually specified polyline spanning the Maharashtra and Kerala portions of the range. This is a screening device, not an official boundary, protected-area boundary, or administrative definition.

Under this proxy:

| Region | Proxy-selected stations | Usable events | Flood | Severe Flood | Catchment coverage |
|---|---:|---:|---:|---:|---:|
| Maharashtra Western Ghats proxy | 20 | 286 | 169 | 117 | 20 / 20 |
| Kerala Western Ghats proxy | 4 | 18 | 13 | 5 | 4 / 4 |

The selected Maharashtra gauge IDs are `585`, `589`, `596`, `602`, `612`, `626`, `635`, `640`, `642`, `643`, `645`, `646`, `648`, `654`, `656`, `668`, `678`, `681`, `682`, and `684`. The selected Kerala IDs are `399`, `403`, `407`, and `441`.

These counts are not final regional labels. The proxy must be replaced or validated against a recognized physiographic boundary before a final case-study claim. The unusually small Kerala subset demonstrates why state-level counting was misleading: Kerala had 531 events across 26 state-filtered stations, but only 18 events across 4 stations under the corridor proxy.

## Compatibility Implications

1. Catchment geometry is available for the proxy-selected Maharashtra and Kerala stations.
2. Geometry is at catchment scale, while the flood events are gauge threshold events; a catchment polygon does not represent observed inundation throughout that polygon.
3. The geometry layer supplies spatial support for rainfall aggregation, DEM feature extraction, and boundary intersection, but not village-level flood labels.
4. Invalid and duplicate geometry groups must be resolved before deriving area, rainfall averages, flow proximity, or village intersections.
5. The current geometry bounds overlap the broad coverage of NASA GPM/POWER, IMD, and ERA5 products, but exact raster-cell overlap has not yet been computed.

## Derived Metadata

The machine-readable result is stored in [data/metadata/catchment_geometry_quality.json](../data/metadata/catchment_geometry_quality.json). The regional screening summary is stored in [data/metadata/ghats_proxy_screening.json](../data/metadata/ghats_proxy_screening.json).

## Required Follow-Up

- Obtain a recognized Western Ghats physiographic boundary or document the chosen proxy against a published source.
- Inspect and repair the three invalid geometries with before/after area checks.
- Investigate the five duplicate WKB geometry groups by GaugeID.
- Obtain administrative boundary layers and calculate actual catchment-boundary intersection.
- Obtain a small, versioned rainfall raster/time-series sample and calculate cell overlap and catchment aggregation.
