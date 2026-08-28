# PRAVAH Phase 1: Local Data-Quality Report

**Inspection date:** 2026-08-28  
**Scope:** Targeted local acquisition and schema/compatibility inspection only. No ML model, forecast system, API, frontend, fake data, or simulated IoT data was created.

## Executive Conclusion

The currently acquired data can support a **gauge/catchment flood-event dataset** for historical analysis and possibly an event-scale or daily forecasting experiment later. It does **not** currently support a defensible 1-hour, 3-hour, or 6-hour village-level flash-flood forecasting target.

The strongest initial case-study candidate is **Maharashtra Western Ghats**, because it has the largest usable INDOFLOODS event set among the tested candidates, all 29 matched stations are marked Open, all 29 have catchment-characteristic rows, and the region lies inside the coverage of the candidate rainfall, DEM, and boundary sources. Kerala is also viable and has 26 open stations with 531 events. Uttarakhand is not currently viable with the public INDOFLOODS release: its six stations are Restricted, produce no matching event rows locally, and the release documentation states that the Ganga and Brahmaputra basins are excluded.

## Acquisition Manifest

| File | Local path | Rows / size | Acquisition status |
|---|---|---:|---|
| `metadata_indofloods.csv` | `data/raw/indofloods/metadata_indofloods.csv` | 214 rows; 40,058 bytes from Zenodo metadata | Acquired |
| `floodevents_indofloods.csv` | `data/raw/indofloods/floodevents_indofloods.csv` | 4,548 rows; 469,728 bytes | Acquired |
| `catchment_characteristics_indofloods.csv` | `data/raw/indofloods/catchment_characteristics_indofloods.csv` | 155 rows; 146,653 bytes | Acquired |
| `precipitation_variables_indofloods.csv` | `data/raw/indofloods/precipitation_variables_indofloods.csv` | 4,548 rows; 677,548 bytes | Acquired |
| `variables_description_indofloods.pdf` | `data/raw/indofloods/variables_description_indofloods.pdf` | 185,357 bytes | Acquired; PDF text extraction tool was unavailable, so semantics requiring the PDF remain conditional |
| `catchments_shapefiles_indofloods.zip` | `data/raw/indofloods/catchments_shapefiles_indofloods.zip` | 664,787 bytes | Acquired and extracted locally for PRJ inspection |
| `India_Flood_Inventory_v3.csv` | `data/raw/ifi/India_Flood_Inventory_v3.csv` | 6,876 rows; 1,801,579 bytes from Zenodo metadata | Acquired |
| `District_FloodImpact.csv` | `data/raw/ifi/District_FloodImpact.csv` | 732 rows; 19,122 bytes | Acquired |
| `District_FloodedArea.csv` | `data/raw/ifi/District_FloodedArea.csv` | 732 rows; 32,567 bytes | Acquired |

Only small published files were downloaded. No rainfall, DEM, administrative-boundary, river, or soil-moisture bulk data was downloaded in this step.

Derived summaries are stored in [data/metadata/local_csv_quality.json](../data/metadata/local_csv_quality.json) and [data/metadata/indofloods_region_summary.json](../data/metadata/indofloods_region_summary.json).

## Exact INDOFLOODS Temporal Precision

### Answers to the required questions

1. **Does an event have only a calendar date?** Yes. The CSV stores `Start Date`, `End Date`, `Peak FL Date`, and, where present, `Peak Discharge Date` as values formatted `YYYY-MM-DD`. Every parsed value has time `00:00:00`; there is no hour, minute, second, timezone, or timestamp-of-observation field.
2. **Does it have an actual timestamp?** No. It has date fields only. The midnight time produced by a parser is a representation of a date, not an observed event time.
3. **Is the start time known?** No. The start calendar date is known for all 4,548 event rows, but the start hour is not known.
4. **Is the peak time known?** No. The peak calendar date is known in `Peak FL Date`; peak hour is not known. `Peak Discharge Date` is available for 3,993 rows and is also date-only.
5. **Can we construct a defensible 1-hour, 3-hour, 6-hour, or 24-hour forecasting target?** Not from these labels alone. A 24-hour target is also not defensible as an observed onset target because the event start and peak hour are unknown. A date-level event target could be constructed only as a separate daily/event-scale experiment with explicit limitations.
6. **Shortest scientifically defensible horizon:** With the current labels, the shortest defensible horizon is **not sub-daily**. The practical minimum is a date-level/daily event formulation, but even that requires a clear prediction cutoff and must not claim hour-level warning lead time. A shorter horizon needs sub-daily or hourly gauge observations and event-onset labels from another source.

### Evidence from local data

- `Start Date`, `End Date`, and `Peak FL Date`: 4,548 valid values each.
- `Peak Discharge Date`: 3,993 valid values; 555 missing.
- No time-of-day or timezone columns exist.
- Event dates range from **1965-07-21** to **2020-09-28**.
- Event durations are integer day fields, not sub-daily durations.

## INDOFLOODS Schema and Quality

### `metadata_indofloods.csv`

- **Rows:** 214
- **Columns:** `GaugeID`, `Warning Level`, `Danger Level`, `Station`, `Latitude`, `Longitude`, `River Name/ Tributory/ SubTributory`, `Basin`, `State`, `Start_date`, `End_date`, `Level_Entries`, `Streamflow_Entries`, `Privacy`, `Source Catchment Area`, `Catchment Area`, `Area variation (%)`, `Reliability`
- **Data types:** identifier/name/geography/privacy/reliability fields are strings; levels, coordinates, entry counts, catchment areas, and variation are numeric; `Start_date` and `End_date` are date strings.
- **Missing values:** `Danger Level` 2 (0.93%); `Basin` 2 (0.93%); `Source Catchment Area` 16 (7.48%); `Area variation (%)` 16 (7.48%); no missing latitude/longitude in the acquired file.
- **Duplicate rows:** 0
- **Duplicate station IDs:** 0; 214 unique `GaugeID` values
- **Coordinates:** latitude 8.1600 to 30.5669; longitude 72.7917 to 91.5919
- **Dates:** `Start_date` 1959-01-01 to 2019-07-01; `End_date` 2006-04-16 to 2020-10-31
- **CRS:** point coordinates are latitude/longitude. No explicit CRS column; compatible with WGS 84 by field convention and matching catchment PRJ metadata, but this must be recorded as an audit assumption.
- **Bounding box:** longitude 72.7917 to 91.5919; latitude 8.1600 to 30.5669.
- **Important access field:** `Privacy` includes `Open` and `Restricted`; this is an access/coverage constraint, not a flood label.

### `floodevents_indofloods.csv`

- **Rows:** 4,548
- **Columns:** `EventID`, `Start Date`, `End Date`, `Peak Flood Level (m)`, `Peak FL Date`, `Num Peak FL`, `Peak Discharge Q (cumec)`, `Peak Discharge Date`, `Flood Volume (cumec)`, `Event Duration (days)`, `Time to Peak (days)`, `Recession Time (day)`, `Flood Type`
- **Data types:** `EventID` and `Flood Type` are strings; date columns are date-only strings; level, counts, discharge, volume, and duration fields are numeric after parsing.
- **Missing values:** peak discharge and peak discharge date each 555 (12.20%); flood volume 577 (12.69%); other fields had no blank values in the local audit.
- **Duplicate rows:** 0
- **Duplicate event IDs:** 0; 4,548 unique `EventID` values
- **Dates:** start 1965-07-21 to 2020-09-24; end 1965-07-21 to 2020-09-28; peak flood date 1965-07-21 to 2020-09-28; peak discharge date 1965-07-21 to 2019-02-12.
- **Unique event types:** `Flood` and `Severe Flood`.
- **Event type distribution:** `Flood` 2,886; `Severe Flood` 1,662.
- **Coordinates:** none in this table; station coordinates must be joined through the gauge encoded in `EventID` and `metadata_indofloods.csv`.
- **CRS and bounding box:** not applicable to the tabular event rows; inherited only after a station/catchment spatial join.
- **Target candidates:** event type, peak level, peak discharge, volume, and duration are target or post-event outcome fields. They must not be used as prediction-time inputs for the same event.

### `catchment_characteristics_indofloods.csv`

- **Rows:** 155
- **Columns:** 108 columns. The key is `GaugeID`; the remaining fields include stream order, flow length, drainage area, catchment relief, catchment geometry, drainage metrics, stream counts/lengths, climate summaries, population, land cover, soil type, and lithology type.
- **Data types:** `GaugeID` and categorical land-cover/soil/lithology/climate fields are strings; measured/derived terrain, drainage, climate, and population fields are numeric.
- **Missing values:** sparse higher-order stream fields. Examples include `No. of Thirdorder Streams` 20 (12.90%), `No. of Fourthorder Streams` 62 (40.00%), `No. of Fifthorder Streams` 94 (60.65%), `No. of Sixthorder Streams` 135 (87.10%), and all `No. of Eigthorder Streams` 155 (100%). Related higher-order stream length and ratio fields have the same pattern.
- **Duplicate rows:** 0
- **Duplicate station IDs:** 0; 155 unique `GaugeID` values
- **Coordinates:** none; geometry is supplied separately in shapefiles.
- **Dates:** none; many climate fields are long-term summaries and must not be treated as current conditions.
- **CRS:** tabular file has no CRS. Join to shapefile geometry only after verifying the PRJ.
- **Geographic bounding box:** not available from the CSV; derive from geometry during the next geospatial audit.
- **Leakage risk:** event-scale or climatological fields need a field-by-field availability audit. Long-term static catchment characteristics are candidates for prediction-time features; variables derived from the event or future period are not.

### `precipitation_variables_indofloods.csv`

- **Rows:** 4,548
- **Columns:** `EventID`, `T1d`, `T2d`, `T3d`, `T4d`, `T5d`, `T6d`, `T7d`, `T8d`, `T9d`, `T10d`
- **Data types:** `EventID` string; `T1d` through `T10d` numeric.
- **Missing values:** 0 in the acquired CSV.
- **Duplicate rows:** 0
- **Duplicate event IDs:** 0; 4,548 unique event IDs
- **Coordinates/CRS/bounding box:** none; spatial join is through `EventID` and station metadata.
- **Dates:** no date column.
- **Interpretation:** the names indicate one- through ten-day precipitation variables, but the exact calculation window, reference date, source product, and whether each value is accumulated before peak/start/event require the variables-description PDF and paper-level documentation. The local CSV alone cannot prove that these are prediction-time observations.
- **Safe feature policy:** until the calculation window and reference time are verified, classify `T1d`-`T10d` as **potentially event-derived/post-event variables** and exclude them from any future model input. They can be reconsidered only if documentation proves that each value was available at the stated prediction cutoff.

### Catchment shapefile ZIP

- **Contents:** per-gauge shapefile components including `.shp`, `.shx`, `.dbf`, and `.prj`; 155 catchment groups were extracted.
- **Geometry:** catchment polygons, with one gauge-linked file group per catchment.
- **CRS:** PRJ files identify WGS 1984 geographic coordinates. Most use `GCS_unknown` with the WGS 1984 datum; some identify `GCS_WGS_1984`. The common geographic CRS is WGS 84, but the inconsistent CRS naming should be normalized during geospatial processing.
- **Duplicate geometry check:** not completed with a GIS engine in this environment; file-group count matches the 155 catchment-characteristic station IDs.
- **Bounding box:** not computed because a GIS reader is not installed. This is a required next local check before spatial joins.
- **Size:** ZIP 664,787 bytes; the full extracted member listing is local only and is not copied into the report.

## IFI Local Schema and Quality

### `India_Flood_Inventory_v3.csv`

- **Rows:** 6,876
- **Columns:** `Unnamed: 0`, `UEI`, `Start Date`, `End Date`, `Duration(Days)`, `Main Cause`, `Location`, `Districts`, `State`, `Latitude`, `Longitude`, `Severity`, `Area Affected`, `Human fatality`, `Human injured`, `Human Displaced`, `Animal Fatality`, `Description of Casualties/injured`, `Extent of damage `, `Event Source`, `Event Souce ID`, `District_LGD_Codes`, `State_Codes`
- **Data types:** `Unnamed: 0`, `UEI`, descriptive fields, cause, district/state, source, and code fields are strings in the raw CSV; date fields are strings formatted `DD-MM-YYYY HH:MM`; duration and impact fields are mixed numeric/string fields requiring typed parsing.
- **Missing values:** `Start Date` 20 (0.29%); `End Date` 20 (0.29%); `Duration(Days)` 19 (0.28%); `Main Cause` 31 (0.45%); `Districts` 60 (0.87%); `District_LGD_Codes` 59 (0.86%); `State_Codes` 258 (3.75%). `Location`, `Latitude`, `Longitude`, `Severity`, `Area Affected`, and `Event Souce ID` are blank in all 6,876 rows in this downloaded v3 file.
- **Impact missingness:** `Human fatality` 3,106 (45.17%); `Human injured` 5,818 (84.61%); `Human Displaced` 6,754 (98.23%); `Animal Fatality` 6,305 (91.70%); casualty description 3,609 (52.49%); extent of damage 3,121 (45.39%).
- **Duplicate rows:** 0 in the raw-row check.
- **Duplicate event key:** `UEI` should be used as the candidate event key; a full duplicate-UEI count was not included in the first summary and must be confirmed before any join.
- **Coordinates:** none usable; latitude and longitude are 100% missing.
- **Dates:** raw values are date-plus-midnight strings, but no valid time-of-day precision is implied. Missing date rows prevent complete temporal use.
- **Event labels/severity:** `Severity` is 100% missing. `Main Cause` contains values such as `flood`, but target semantics require further documentation.
- **CRS/bounding box:** not applicable because coordinates are entirely missing.
- **Use:** historical/context and possible district-level validation only. It cannot provide spatial point labels or short-term prediction targets in its present form.

### `District_FloodImpact.csv`

- **Rows:** 732
- **Columns:** `Dist_Name`, `Human_fatality`, `Human_injured`, `Population`, `Mean_Flood_Duration`
- **Data types:** district name string; impact/population/duration fields numeric after parsing.
- **Missing values:** `Mean_Flood_Duration` 11 (1.50%); other fields had no blanks.
- **Duplicate rows:** 0. District-name uniqueness and historical district versioning require a separate key audit.
- **Coordinates/CRS/dates:** none.
- **Use:** district-level impact and exposure context; not a forecast label.

### `District_FloodedArea.csv`

- **Rows:** 732
- **Columns:** `Dist_Name`, `Percent_Flooded_Area`, `Parmanent_Water`, `Corrected_Percent_Flooded_Area`
- **Data types:** district name string; three area-percentage fields numeric after parsing.
- **Missing values:** 0 in the local raw-row check.
- **Duplicate rows:** 0; district-name uniqueness/versioning still requires audit.
- **Coordinates/CRS/dates:** none.
- **Use:** static/long-term district flood-area context and validation; not a short-term forecast label.

## Prediction-Time, Post-Event, and Target Variables

### A. Potential prediction-time features

These can be considered only after availability timing is verified:

- Current or lagged rainfall observations from an external rainfall product.
- Current stream level/discharge observations, if a live or historical time series is obtained.
- Static catchment characteristics such as drainage area, relief, stream order, land cover, soil type, and lithology, subject to provenance and missingness checks.
- DEM-derived terrain features from SRTM or another verified DEM.
- River/catchment geometry and administrative/exposure layers.
- Soil-moisture values only when their observation time and latency are known.

### B. Post-event or potentially post-event variables

- `Peak Flood Level (m)` and `Peak FL Date`.
- `Peak Discharge Q (cumec)` and `Peak Discharge Date`.
- `Flood Volume (cumec)`.
- `Event Duration (days)`, `Time to Peak (days)`, and `Recession Time (day)`.
- `Flood Type` when used as an outcome label.
- IFI impacts, casualties, flooded-area percentages, and DFSI-type summaries.
- INDOFLOODS `T1d`-`T10d` until the documentation proves they are computed strictly from data available before the prediction cutoff.
- Any catchment characteristic that is event-derived or calculated using a future period rather than a fixed pre-event baseline.

### C. Target variables

Possible targets for a later, explicitly scoped experiment are:

- Daily/event occurrence at a gauge: `Flood Type` or threshold exceedance.
- Peak level or peak discharge, where available, as a gauge-level regression target.
- Event severity class, with the caveat that `Flood` versus `Severe Flood` is a source-defined label, not a validated flash-flood severity scale.

The current data does not justify a village-level inundation target or a sub-daily flash-flood target.

## Candidate Region Comparison

Region filters use the `State` field in `metadata_indofloods.csv`. “Western Ghats” is approximated by state-level screening here; it is not a final physiographic boundary selection.

| Candidate | Stations | Open / Restricted | Events | Usable events | Event date range | Event types | Severe events | Missing discharge / volume | Catchment rows | Rainfall-variable rows | Assessment |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---|
| Kerala Western Ghats | 26 | 26 / 0 | 531 | 531 | 1971-06-25 to 2019-08-20 | Flood 340; Severe Flood 191 | 191 | 41 / 43 | 26 | 531 | Meaningful gauge/catchment case study is plausible; short-term flash-flood target is not currently supported |
| Maharashtra Western Ghats screening | 29 | 29 / 0 | 817 | 817 | 1965-08-01 to 2020-05-27 | Flood 436; Severe Flood 381 | 381 | 42 / 56 | 29 | 817 | Strongest current candidate for a gauge/catchment study; state-level filter includes areas outside the Western Ghats |
| Uttarakhand | 6 | 0 / 6 | 0 | 0 | No matching published event rows | None | 0 | 0 / 0 | 0 | 0 | Not viable with the public INDOFLOODS release; Ganga exclusion and Restricted stations are decisive |

### Region spatial compatibility

- **Rainfall:** all three candidate state bounding boxes lie inside the broad coverage of GPM IMERG and ERA5. IMD’s India grid also covers the three bounding boxes. This is coverage overlap only; no rainfall files were downloaded or spatially joined yet.
- **Terrain:** SRTMGL1 coverage includes all three regions. No SRTM tiles were downloaded in this step.
- **Administrative boundaries:** no boundary files were downloaded in this step. Spatial overlap is therefore not locally measured; it is only a source-coverage expectation.
- **Catchments:** Kerala and Maharashtra have a one-to-one count of state-filtered station IDs and catchment-characteristic rows. Uttarakhand has none in the public catchment file.
- **Station bounding boxes:** Kerala longitude 75.1472-76.9200, latitude 8.7150-12.4792; Maharashtra screening longitude 73.1108-79.6478, latitude 16.6753-21.0719; Uttarakhand longitude 78.1900-79.5525, latitude 29.9800-30.5669.

### Why Maharashtra is recommended over Kerala

Maharashtra has 817 usable events versus Kerala’s 531 and 381 severe-labelled events versus 191. Both have complete Open station coverage for their state-filtered stations and matching catchment rows. This is a data-availability recommendation, not a claim that Maharashtra is intrinsically more flash-flood-prone or that the state-wide station set represents the Western Ghats uniformly.

Before final selection, the state-level Maharashtra filter must be narrowed to an actual Western Ghats subregion using catchment geometry, terrain, administrative boundaries, and rainfall overlap. Kerala remains the fallback candidate if the narrowed Maharashtra subset loses too many events or has weak topographic/rainfall alignment.

## Join Feasibility

### Joins that are currently plausible

- `floodevents_indofloods.EventID` to gauge ID encoded in the event key.
- Gauge ID in events to `metadata_indofloods.GaugeID` after normalizing the `INDOFLOODS-gauge-` prefix.
- Gauge ID to `catchment_characteristics_indofloods.GaugeID` for the 155 available catchments.
- Gauge-linked catchment shapefile to metadata and characteristics after verifying geometry count and bounds.
- Event ID to `precipitation_variables_indofloods.EventID`.

### Joins that are not yet defensible

- INDOFLOODS events to village/ward units: no village/ward boundaries acquired and gauge events are not areal village flood labels.
- INDOFLOODS event labels to hourly rainfall: dates have no event hour, so an hourly causal alignment cannot be established.
- INDOFLOODS event precipitation to prediction-time inputs: exact reference window and publication timing of `T1d`-`T10d` are not yet verified.
- IFI point-level spatial joins: coordinates are entirely missing in the acquired v3 main CSV.
- District impact tables to current administrative boundaries: names and boundary vintages may differ; LGD/code reconciliation is required.

## Recommendation Summary

**A. Best case-study region:** Maharashtra Western Ghats screening area, narrowed to catchments that are actually inside the Western Ghats after geometry/DEM/boundary inspection. Kerala is the fallback. Uttarakhand is deferred unless an additional usable Ganga-basin event/streamflow source is obtained.

**B. Best usable flood-event dataset:** INDOFLOODS v1.0, for gauge/catchment event analysis. It is not a direct village-level inundation dataset.

**C. Best rainfall source:** NASA GPM IMERG for a future sub-daily rainfall comparison, with a single documented run/version and product latency recorded. It does not solve the missing sub-daily flood labels.

**D. Best hydrological/soil-moisture source:** an accessible historical or near-real-time streamflow/level series aligned to the selected INDOFLOODS gauges. No such additional series has yet been acquired. Copernicus global Soil Water Index is a secondary, coarse antecedent-moisture candidate, not a substitute for local hydrology.

**E. Defensible forecast horizon:** no sub-daily horizon is currently defensible. The shortest possible next phase is a date-level/daily gauge-event formulation, only after a prediction cutoff and label construction protocol are documented. This should not be described as 1-, 3-, or 6-hour flash-flood prediction.

**F. Proposed modelling spatial unit:** gauge-linked catchment as the primary unit. Results may later be intersected or aggregated to villages/wards for display, but that would not create true village-level labels.

**G. Is true short-term flash-flood forecasting feasible with currently available data?** **No.** The current INDOFLOODS labels are date-only, station/gauge based, and contain missing discharge/volume values. The current package does not establish event onset within a day or provide village-level inundation observations.

**H. Missing data that prevents it:** sub-hourly or hourly observed rainfall and streamflow/level series with timestamps; event onset and peak timestamps; spatially resolved flood extent or village-level event labels; accessible Ganga-basin data if Uttarakhand is selected; verified administrative boundaries; and documentation proving that every input feature was available before the prediction cutoff.

## Next Step After Review

The next technical step should remain data-only:

1. Install or use a GIS-capable reader solely for local geometry bounds, validity, and CRS checks.
2. Narrow Maharashtra and Kerala to actual Western Ghats catchments using the acquired catchment polygons and a limited DEM/boundary sample.
3. Verify the INDOFLOODS variables-description PDF and paper to classify `T1d`-`T10d` as pre-event or post-event.
4. Obtain a small, timestamped rainfall sample and one accessible timestamped hydrological series for the shortlisted catchments.
5. Recompute exact cross-source spatial and temporal overlap.
6. Decide whether the project can honestly proceed with daily gauge-event forecasting, or must be framed as historical flood-risk/susceptibility analysis until better labels are obtained.

No model training or application implementation should begin before these checks are complete.
