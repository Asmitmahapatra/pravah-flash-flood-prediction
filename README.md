# PRAVAH — Multi-Source Flash-Flood Prediction System

PRAVAH is a data-driven AI and geospatial system for flash-flood prediction and early warning in hilly regions of India.

---

## Verified Study Region Definition & Master Daily Grid (Phase 1 & Phase 2)

- **Target Region:** Maharashtra Western Ghats (100 km Crest Line Corridor Proxy)
- **Target Stations / Catchments:** 20 Open Gauge Stations
- **Verified Target GaugeIDs:** `585`, `589`, `596`, `602`, `612`, `626`, `635`, `640`, `642`, `643`, `645`, `646`, `648`, `654`, `656`, `668`, `678`, `681`, `682`, `684`
- **Master Daily Spatio-Temporal Grid Size:** **201,344 gauge-days** (1964-12-01 to 2020-05-27)
- **Primary Relational Key:** `(GaugeID, Date)` composite key (0 duplicates, 0 nulls)

---

## Phase 2 Target Labels & Event Totals

| Target Column | Description | No Event (`0`) | Flood (`1`) | Severe Flood (`2`) | Total Positive Days |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `target_onset` | Event Onset Day (`Start Date`) | 201,058 | 169 | 117 | **286** |
| `target_active` | Event Active Duration (`Start Date` to `End Date`) | 199,963 | 647 | 734 | **1,381** |
| `target_peak` | Event Peak Day (`Peak FL Date`) | 201,058 | 169 | 117 | **286** |

- **Total Event-Day Assignments:** 1,381 days
- **Unique Active Gauge-Days:** 1,381 days
- **Overlapping Collision Count:** 0 collisions across all 286 events
- **Observation Bounds:** Negative labels (`0`) generated strictly within `[Start_date, End_date]` per station from `target_metadata.csv`. No negative labels fabricated outside operational observation windows.
- **Leakage Prevention:** Prohibited post-event columns (`Peak Discharge`, `Peak FL`, `Volume`, `Duration`) and event-only `T1d`-`T10d` rainfall features are strictly excluded from predictors.

---

## Repository Layout & Data Pipeline

```
PRAVAH/
├── README.md                                    # Project description & Phase 2 dataset specifications
├── docs/                                        # Phase 1 audit & validation documentation
├── data/
│   ├── raw/                                     # Immutable archives (INDOFLOODS v1.0 & IFI v3)
│   ├── metadata/                                # Validation JSON summaries
│   └── processed/                               # Cleaned & processed datasets
│       ├── clean_catchments.geojson             # 155 valid catchments (EPSG:4326)
│       ├── target_catchments.geojson            # 20 target region catchments
│       ├── target_metadata.csv                  # 20 target station metadata rows
│       ├── target_floodevents.csv               # 286 target region flood events
│       ├── target_catchment_characteristics.csv # 20 target region catchment attribute rows
│       ├── target_precipitation_variables.csv   # 286 target region antecedent precipitation rows
│       ├── master_daily_grid.csv                # Master Date x GaugeID daily modeling grid (201,344 rows)
│       ├── master_daily_grid.csv.gz             # Compressed daily modeling grid archive
│       └── daily_grid_summary.json              # Machine-readable Phase 2 validation summary
└── src/
    └── data/                                    # Data processing modules
        ├── clean_catchment_geometries.py        # Geometry repair & validation script
        ├── filter_target_region.py              # Regional filtering & integrity verification script
        └── construct_daily_grid.py              # Daily spatio-temporal grid construction script
```

---

## Progress Status & Milestones

### Completed:
- [x] **Phase 1 Audit & Validation:** Full data profiling, catchment geometry repair (3 invalid geometries fixed, 5 duplicate pairs preserved), temporal precision audit, leakage audit.
- [x] **Phase 1.5 Regional Harmonization:** Filtered all INDOFLOODS layers to the 20 target Maharashtra Western Ghats catchments (286 events).
- [x] **Phase 2 Master Daily Grid Construction:** Built `master_daily_grid` (201,344 rows), dynamically calculated expected bounds, mapped three target formulations (`target_onset`, `target_active`, `target_peak`), joined static catchment characteristics (121 columns), and passed all 8 fail-fast empirical validation checks.

### Pending / Next Steps:
- [ ] **Sub-Daily Precipitation Retrieval & Spatial Clipping:** Download NASA GPM IMERG or ERA5 daily precipitation rasters for the target catchments to construct uniform rainfall predictor features across all 201,344 gauge-days.
- [ ] **Chronological Train / Validation / Test Splitting:** Implement temporal splitting strategy for ML evaluation.
- [ ] **ML Baseline Pipeline:** Train initial benchmark model (e.g. LightGBM / XGBoost / Random Forest) on the daily modeling grid.
