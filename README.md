# PRAVAH — Multi-Source Flash-Flood Prediction System

PRAVAH is a data-driven AI and geospatial system for flash-flood prediction and early warning in hilly regions of India.

---

## Study Region Definition & Master Daily Modeling Grid (Phase 1 & Phase 2)

- **Target Region:** Maharashtra Western Ghats (100 km Crest Line Corridor Proxy)
- **Target Stations / Catchments:** 20 Open Gauge Stations
- **Verified Target GaugeIDs:** `585`, `589`, `596`, `602`, `612`, `626`, `635`, `640`, `642`, `643`, `645`, `646`, `648`, `654`, `656`, `668`, `678`, `681`, `682`, `684`
- **Master Daily Spatio-Temporal Grid Size:** **201,344 gauge-days** (1964-12-01 to 2020-05-27)
- **Primary Relational Key:** `(GaugeID, Date)` composite key (0 duplicates, 0 nulls)
- **Total Features & Targets:** 131 columns + `split` column (132 total)
  - 3 dynamic flood target formulations (`target_onset`, `target_active`, `target_peak`)
  - 10 pre-cutoff antecedent rainfall features (IMD 0.25° gridded daily rainfall, area-overlap weighted zonal mean)
  - 107 static catchment morphology, climatic, socio-economic, soil, lithology, and land-cover descriptors
  - Station metadata and coordinates

---

## Phase 2 Target Formulations & Class Counts

| Target Column | Description | No Event (`0`) | Flood (`1`) | Severe Flood (`2`) | Total Positive Days | Positive Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `target_onset` | Event Onset Day (`Start Date`) | 201,058 | 169 | 117 | **286** | 0.142% |
| `target_active` | Event Active Duration (`Start Date` to `End Date`) | 199,963 | 647 | 734 | **1,381** | 0.686% |
| `target_peak` | Event Peak Day (`Peak FL Date`) | 201,058 | 169 | 117 | **286** | 0.142% |

- **Total Event-Day Assignments:** 1,381 days
- **Unique Active Gauge-Days:** 1,381 days (0 overlapping collision days across all 286 events)
- **Observation Bounds:** Negative labels (`0`) generated strictly within `[Start_date, End_date]` per station from `target_metadata.csv`. No negative labels fabricated outside operational observation windows.
- **Leakage Prevention:** Prohibited post-event columns (`Peak Discharge`, `Peak FL`, `Volume`, `Duration`) and event-only `T1d`-`T10d` rainfall features are strictly excluded from predictors. All daily precipitation features strictly use rainfall accumulated on or before Day $T-1$.

---

## Phase 2C Chronological Train / Validation / Test Splits

| Split | Date Range | Operating Gauges | Total Gauge-Days | Split Share | Onset Positive Days (Rate) | Active Flood Days (Rate) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 1964-12-01 to 2010-12-31 | 10 legacy stations | 155,976 | 77.47% | 234 (0.150%) | 960 (0.616%) |
| **Validation** | 2011-01-01 to 2015-12-31 | 12 stations | 19,783 | 9.83% | 8 (0.040%) | 38 (0.192%) |
| **Test** | 2016-01-01 to 2020-05-27 | 20 stations | 25,585 | 12.71% | 44 (0.172%) | 383 (1.497%) |
| **TOTAL** | **1964-12-01 to 2020-05-27** | **20 stations** | **201,344** | **100.0%** | **286 (0.142%)** | **1,381 (0.686%)** |

- **Split Disjointness:** Strictly 0 overlapping dates across partitions.
- **Chronological Progression:** Train max date (`2010-12-31`) < Validation min date (`2011-01-01`) < Test min date (`2016-01-01`).
- **Zero Boundary Leakage:** Validation features on 2011-01-01 strictly use antecedent rainfall $\le$ 2010-12-31.
- **Station Progression Audit:** Reflects historical commissioning of CWC gauge stations in Maharashtra Western Ghats (10 in 1964–1979, 2 commissioned in 2013–2014, 8 commissioned in 2016–2019).

---

## Phase 3 Machine Learning Benchmark Results (Out-of-Sample Test Set 2016–2020)

### Task A: 1-Day Ahead Flood Onset (`target_onset > 0`)
| Model | Threshold | Precision | Recall | F1 Score | CSI | ROC-AUC | PR-AUC (Avg Precision) | Model Artifact |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **RandomForest** | `0.2935` | 3.20% | 15.91% | **0.0532** | **0.0273** | **0.8384** | **0.0629** | `models/task_a_onset_RandomForest.joblib` |
| **XGBoost** | `0.8210` | 6.33% | 11.36% | **0.0813** | **0.0424** | 0.7935 | 0.0421 | `models/task_a_onset_XGBoost.joblib` |
| **LightGBM** | `0.0000` | 0.17% | 100.0% | 0.0034 | 0.0017 | 0.8102 | 0.0105 | `models/task_a_onset_LightGBM.joblib` |

### Task B: Daily Active Flood State (`target_active > 0`)
| Model | Threshold | Precision | Recall | F1 Score | CSI | ROC-AUC | PR-AUC (Avg Precision) | Model Artifact |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **XGBoost** | `0.9700` | **22.10%** | 15.40% | **0.1815** | **0.0998** | 0.6744 | 0.0792 | `models/task_b_active_XGBoost.joblib` |
| **LightGBM** | `0.9490` | 11.47% | **25.07%** | 0.1574 | 0.0854 | **0.7552** | 0.0693 | `models/task_b_active_LightGBM.joblib` |
| **RandomForest** | `0.5425` | 13.22% | 16.71% | 0.1476 | 0.0797 | 0.7036 | **0.0821** | `models/task_b_active_RandomForest.joblib` |

---

## Phase 4 & Phase 5: REST API & Interactive Streamlit Dashboard

### 3. React Operations Dashboard

The recommended operator interface is the React/TypeScript client in `frontend/`. It keeps the Python inference engine and FastAPI service, while providing a richer control-room experience with live catchment mapping, historical replay, model provenance, and responsive controls.

Start the API first:

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

Then start the React client in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/`. The original Streamlit dashboard remains available with the command below for notebook-style exploration.

### 1. Launching the Interactive Web Dashboard:
```bash
streamlit run src/dashboard/app.py
```
Opens an interactive dashboard with:
- 🗺️ **Live Risk & Catchment Map:** Folium Leaflet map with colored alert tiers & live 10-day rainfall scenario simulator.
- ⏳ **Historical Simulation Replay:** Scrub through 1964–2020 dates to replay predicted vs. CWC ground truth flood states.
- 📊 **Model Benchmarks & Explainability:** ROC/PR metrics & Plotly horizontal top 15 feature importance charts.
- 🛰️ **Catchment Geospatial Telemetry:** Full morphometric, demographic, road density, soil, and land-cover profiles.

### 2. Launching the FastAPI REST Service:
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger Documentation: `http://localhost:8000/docs`

---

## Repository Layout & Pipeline Architecture

```
PRAVAH/
├── README.md                                    # Project description & usage guide
├── docs/                                        # Phase 1 audit & validation documentation
├── data/
│   ├── raw/                                     # Immutable archives (INDOFLOODS v1.0, IFI v3, IMD NetCDF)
│   │   ├── indofloods/                          # Raw shapefiles & CSVs
│   │   ├── ifi/                                 # India Flood Inventory raw tables
│   │   └── imd_rainfall/                        # 57 yearly NetCDF files (1964–2020)
│   ├── metadata/                                # Validation JSON summaries
│   └── processed/                               # Cleaned & processed datasets
│       ├── clean_catchments.geojson             # 155 valid catchments (EPSG:4326)
│       ├── target_catchments.geojson            # 20 target region catchments
│       ├── target_metadata.csv                  # 20 target station metadata rows
│       ├── target_floodevents.csv               # 286 target region flood events
│       ├── target_catchment_characteristics.csv # 20 target region catchment attribute rows
│       ├── target_precipitation_variables.csv   # 286 target region antecedent precipitation rows
│       ├── target_catchment_daily_rainfall.csv  # 20 catchments x 1964–2020 daily rainfall
│       ├── master_daily_grid.csv                # Master Date x GaugeID grid (201,344 rows x 121 cols)
│       ├── master_daily_grid_with_rainfall.parquet # Daily grid + rainfall features (131 cols)
│       ├── master_daily_grid_splits.parquet     # Master grid with 'split' column (132 cols, snappy)
│       ├── master_daily_grid_splits.csv.gz      # Compressed archive with 'split' column
│       ├── daily_grid_summary.json              # Phase 2A validation report
│       ├── rainfall_pipeline_summary.json       # Phase 2B validation report
│       ├── splits_summary.json                  # Phase 2C validation report
│       ├── model_evaluation_metrics.json        # Phase 3 model benchmark report
│       └── feature_importance_*.png             # Top 15 feature importance charts
├── models/                                      # Serialized trained model binaries
│   ├── task_a_onset_RandomForest.joblib         # Best Onset model (ROC-AUC 0.8384)
│   ├── task_a_onset_XGBoost.joblib              # Onset XGBoost pipeline
│   ├── task_a_onset_LightGBM.joblib             # Onset LightGBM pipeline
│   ├── task_b_active_XGBoost.joblib             # Best Active model (F1 0.1815, CSI 0.0998)
│   ├── task_b_active_LightGBM.joblib            # Active LightGBM pipeline
│   └── task_b_active_RandomForest.joblib        # Active Random Forest pipeline
├── tests/                                       # Data integrity, API & dashboard test suite
│   ├── test_pravah_data_integrity.py            # Unit tests for data schemas & feature guards
│   ├── test_inference_and_api.py                # Unit & API integration test suite
│   └── test_dashboard.py                        # Dashboard compilation & syntax test
└── src/
    ├── data/                                    # Data processing modules
    │   ├── clean_catchment_geometries.py        # Geometry repair & validation script
    │   ├── filter_target_region.py              # Regional filtering & integrity verification script
    │   ├── construct_daily_grid.py              # Daily spatio-temporal grid construction script
    │   ├── download_and_aggregate_rainfall.py   # IMD rainfall download & zonal aggregation script
    │   └── create_temporal_splits.py            # Chronological temporal splitting script
    ├── model/                                   # Machine learning training & evaluation
    │   ├── baseline_flood_model.py              # Baseline model prototype
    │   └── train_classifiers.py                 # Multi-model training, threshold tuning & export
    ├── inference/                               # Real-time inference engine
    │   └── predictor.py                         # PravahInferenceEngine class
    ├── api/                                     # FastAPI REST backend service
    │   ├── app.py                               # Route definitions and application server
    │   └── schemas.py                           # Pydantic request/response schemas
    └── dashboard/                               # Streamlit Interactive Web Application
        └── app.py                               # Multi-tab geospatial dashboard & live simulator
```

---

## Progress Status & Milestones

### Completed:
- [x] **Phase 1 Audit & Validation:** Full data profiling, catchment geometry repair (3 invalid geometries fixed, 5 duplicate pairs preserved), temporal precision audit, leakage audit.
- [x] **Phase 1.5 Regional Harmonization:** Filtered all INDOFLOODS layers to the 20 target Maharashtra Western Ghats catchments (286 events).
- [x] **Phase 2A Master Daily Grid Construction:** Built `master_daily_grid` (201,344 rows), dynamically calculated expected bounds, mapped three target formulations (`target_onset`, `target_active`, `target_peak`), joined static catchment characteristics (121 columns), and passed all 8 fail-fast empirical validation checks.
- [x] **Phase 2B Precipitation Pipeline:** Downloaded 57 years of IMD 0.25° daily gridded rainfall (1964–2020), executed EPSG:6933 equal-area zonal aggregation for all 20 catchments, engineered 9 antecedent rainfall features (strictly $\le T-1$, 0 leakage), and exported `master_daily_grid_with_rainfall.parquet`.
- [x] **Phase 2C Chronological Splitting:** Implemented non-leaking chronological Train (1964–2010: 155,976 rows), Validation (2011–2015: 19,783 rows), and Test (2016–2020: 25,585 rows) partitions with automated validation checks and summary export.
- [x] **Phase 3 ML Benchmark & Checkpoints:** Trained Random Forest, LightGBM, and XGBoost classifiers on Onset and Active flood tasks, optimized decision thresholds on Validation, evaluated on Test (2016–2020), and serialized all fitted models into `models/`.
- [x] **Phase 4 Inference Engine & REST API:** Built `PravahInferenceEngine` and FastAPI backend service (`src/api/app.py`) supporting live risk scoring, GeoJSON catchment telemetry, and historical simulation replays.
- [x] **Phase 5 Interactive Web Dashboard:** Built multi-tab Streamlit dashboard (`src/dashboard/app.py`) with interactive Leaflet catchment risk map, live rainfall scenario simulator, historical simulation replay slider, and feature explainability charts. 14/14 automated tests passing.
