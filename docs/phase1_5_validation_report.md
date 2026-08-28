# PRAVAH Phase 1.5: Spatial, Temporal, and Leakage Validation

**Inspection date:** 2026-08-28  
**Scope:** Validation only. No model, API, frontend, prediction system, fake data, flood-label simulation, or IoT simulation was created.

## Executive Decision

The current sources can be joined into a **gauge-linked catchment historical analysis table**, but they cannot yet form a scientifically defensible short-term flash-flood forecasting dataset.

The strongest current study area is a **Maharashtra Western Ghats catchment subset**, selected with a transparent 100 km crest-corridor screening proxy rather than the entire state. It has 20 proxy-selected stations, 286 usable INDOFLOODS events, and 20 matching catchment polygons. Kerala has only 4 proxy-selected stations and 18 events under the same style of corridor screening. This recommendation remains conditional on replacing the proxy with a recognized physiographic boundary and checking actual rainfall/hydrological coverage.

The critical blocker is temporal: INDOFLOODS event labels contain calendar dates only. The current data does not identify flood onset or peak within a day. Rainfall and soil-moisture samples can be retrieved hourly, but that does not create hourly flood labels. There is also no continuous timestamped streamflow/water-level series available in the acquired INDOFLOODS package.

## 1. INDOFLOODS Precipitation Leakage Audit

The detailed audit is in [docs/indofloods_precipitation_leakage_audit.md](indofloods_precipitation_leakage_audit.md).

The local variables-description PDF defines:

- `T1d`: daily precipitation one day before the flood start date.
- `T2d`-`T10d`: cumulative daily precipitation for the preceding 2 through 10 days before the flood start date.
- Units: millimetres.
- Source: corrected mean of ERA5 daily precipitation probabilistic estimates at 0.1 degree spatial resolution, according to the PDF. The PDF cites Tang et al. (2022).

All T variables are therefore **pre-flood-start by documented definition**, not event-total or post-peak variables. However, the CSV does not store the product version, exact daily time boundary, timezone, retrieval time, or operational availability. Every variable is classified:

> **POTENTIALLY SAFE - REQUIRES ASSUMPTION**

They must not be used in a model until the exact source/version and prediction-time availability are reproduced. A retrospective antecedent feature is not automatically an operationally available feature.

## 2. Catchment GIS Quality

The detailed result is in [docs/geospatial_quality_report.md](geospatial_quality_report.md). Derived metadata is in [data/metadata/catchment_geometry_quality.json](../data/metadata/catchment_geometry_quality.json).

| Check | Result |
|---|---:|
| Geometry features | 155 |
| Invalid geometries | 3 |
| Empty geometries | 0 |
| Exact duplicate geometries | 5 duplicate rows; 150 unique WKB geometries |
| Unique source/GaugeID values | 155 |
| Geographic bounds | 72.695E-91.975E, 8.175N-28.250N |
| Catchment area range | 34.03 km2 to 308,209.25 km2 |
| CRS | WGS 84; normalized to EPSG:4326 |

All 155 catchment source IDs match the 155 characteristic-table GaugeIDs after prefix normalization. The 214-station metadata table is larger than the catchment geometry table. Three invalid geometries and five duplicate geometry groups must be investigated before geometry-derived features are used.

## 3. Maharashtra vs Kerala Western Ghats

The entire state was not labelled as the Western Ghats. Because no authoritative machine-readable Ghats boundary was acquired, the current screen uses a documented **100 km corridor around an approximate Western Ghats crestline**. This is a physiographic screening proxy, not an official boundary.

| Region | Proxy stations | Open / Restricted | Usable events | Flood | Severe Flood | Catchment coverage | Assessment |
|---|---:|---:|---:|---:|---:|---:|---|
| Maharashtra Western Ghats proxy | 20 | 20 / 0 | 286 | 169 | 117 | 20 / 20 | Best current data-supported candidate, pending boundary validation |
| Kerala Western Ghats proxy | 4 | 4 / 0 | 18 | 13 | 5 | 4 / 4 | Too few proxy-selected events for a robust first study, but retain as fallback |

The state-level counts were misleading: Maharashtra had 817 events across 29 state-filtered stations and Kerala had 531 across 26, but many of those stations are outside the approximate Ghats corridor. The proxy-selected Maharashtra catchments include IDs `585`, `589`, `596`, `602`, `612`, `626`, `635`, `640`, `642`, `643`, `645`, `646`, `648`, `654`, `656`, `668`, `678`, `681`, `682`, and `684`. Kerala includes `399`, `403`, `407`, and `441`.

Both proxy regions have broad coverage overlap with the candidate rainfall products and SRTM. Exact raster-cell and administrative-boundary intersection is still pending because no regional rainfall or boundary vector was downloaded. The recommendation is based on event/catchment availability plus plausible terrain coverage, not event count alone.

## 4. Small Rainfall Sample Feasibility

A small NASA POWER hourly sample was retrieved for three candidate gauges:

- Gauge 643, Terwad, Maharashtra: 16.6753N, 74.5736E
- Gauge 681, Samdoli, Maharashtra: 16.8550N, 74.4967E
- Gauge 403, Kuttyadi, Kerala: 11.6250N, 75.7844E

Each request covered **2019-07-01 through 2019-07-03**, 72 hourly records per point, using the NASA POWER hourly point API. Files are stored as [data/metadata/nasa_power_643.json](../data/metadata/nasa_power_643.json), [data/metadata/nasa_power_681.json](../data/metadata/nasa_power_681.json), and [data/metadata/nasa_power_403.json](../data/metadata/nasa_power_403.json).

| Property | Result |
|---|---|
| Product | NASA POWER Analysis Ready Data hourly API v2.9.9 documentation |
| Requested parameters | `PRECTOTCORR`, `GWETTOP` |
| Temporal resolution | Hourly |
| Timestamp convention | Response keys are `YYYYMMDDHH`; API defaults to Local Solar Time, while UTC can be requested explicitly. The sample request used the documented default and must be repeated with `time-standard=UTC` for modelling. |
| Spatial representation | Point retrieval at requested gauge coordinates; underlying parameter native resolutions are not encoded in the sample JSON |
| Rainfall units | NASA POWER hourly documentation states precipitation values are shown in mm/hour |
| Soil-wetness units | `GWETTOP` values are returned in the approximate 0-1 range; the exact parameter definition/units must be recorded from the parameter catalogue before use |
| Time coverage | Hourly API documentation: 2001-01-01 to near real time |
| Availability | NASA POWER provides an analysis-ready historical API; operational latency and revision policy must be recorded for the chosen production use |
| Missingness in sample | 0 missing values for both requested parameters at all three points |
| Rainfall range in sample | Gauge 643: 7.21-43.38; gauge 681: 4.67-45.50; gauge 403: 2.30-17.80, in the API’s precipitation units |
| `GWETTOP` range in sample | Gauge 643: 0.82-0.90; gauge 681: 0.75-0.92; gauge 403: 0.82-0.87 |

This proves that a small timestamped rainfall/soil-wetness query can be aligned to gauge coordinates. It does **not** prove that NASA POWER rainfall is equivalent to the INDOFLOODS T variables, nor that its spatial resolution is sufficient for village-level prediction. The eventual rainfall product must be fixed and versioned, and all timestamps must be converted to an explicit standard such as UTC.

NASA GPM IMERG remains a candidate for sub-daily rainfall because its official documentation describes half-hourly Early, Late, and Final products. No GPM bulk archive was downloaded in this step. The NASA POWER sample was used only as a documented small feasibility test.

## 5. Hydrological Data Feasibility

INDOFLOODS contains event summaries and metadata, not a continuous timestamped observation series. The event table has peak level/discharge and event dates, but 555 discharge values and 577 volume values are blank. The event dates have no time-of-day.

The Central Water Commission documents a national flood-forecasting network that observes water levels/discharges and provides hydrological data through a request process. Its hydrological-data page states that release requests require a data-request form, purpose/geographical scope, and, in relevant cases, secrecy undertakings. This is evidence that potentially useful observations exist, not evidence that the needed station series are publicly downloadable for PRAVAH.

**Result:** no accessible continuous timestamped historical streamflow or water-level series was obtained for the shortlisted INDOFLOODS gauges in this validation step. CWC/India-WRIS is the most credible acquisition route to investigate next. Until a matching series is obtained, INDOFLOODS peak values must remain labels/outcomes and cannot be treated as continuous predictors.

## 6. Soil-Moisture Feasibility

The practical small-sample option tested was NASA POWER `GWETTOP`, retrieved together with hourly precipitation for the three gauges above. It provides 72 timestamped values per gauge with no missing values in the sample and can serve as a candidate antecedent wetness feature.

For a more explicitly documented land-surface source, ERA5-Land provides global hourly data from 1950-present on a 0.1 degree grid, with soil layers extending to 289 cm and CC BY licensing. It is a model/reanalysis estimate rather than a local sensor observation. The source is temporally compatible with a daily/event-scale experiment, but its coarse spatial resolution and reanalysis uncertainty limit village-level interpretation.

**Result:** historical gridded antecedent moisture is feasible. Local observed soil moisture is not yet available. The soil-moisture variable, depth/layer, units, product version, and latency must be fixed before use.

## 7. Forecast-Horizon Feasibility

| Target | Feasible now? | Reason |
|---|---|---|
| 1-hour forecast | **No** | Flood labels have no hour; no continuous matching streamflow/level series is available; rainfall alone cannot supply the target label |
| 3-hour forecast | **No** | Same temporal-label and hydrological-observation gap |
| 6-hour forecast | **No** | Same gap; daily event start cannot be assigned to a six-hour interval |
| 24-hour forecast | **No for a defensible observed onset target** | Rainfall/soil samples can be hourly, but INDOFLOODS only identifies event dates and lacks start hour; a 24-hour target would require an explicit date-level reformulation, not an hourly onset claim |
| Daily flood-event prediction | **Conditionally possible** | INDOFLOODS provides date-level event labels and station/catchment linkage, but the prediction cutoff, negative examples, feature timing, and rainfall/streamflow availability still need formal construction |

The current shortest scientifically defensible formulation is a **daily/date-level gauge-event study**, not a short-term flash-flood warning system. This conclusion is driven by actual label precision and missing continuous hydrology, not by a preference for a longer horizon.

## 8. Proposed First Modelling Table

This is a design proposal only. No table has been built and no model will be trained yet.

| Field | Proposed definition |
|---|---|
| ROW | One gauge-linked catchment at one explicit daily prediction cutoff timestamp |
| TARGET | Whether the gauge records a qualifying flood event on the defined target date/window, using a source-defined event label |
| TIME OF PREDICTION | A documented daily cutoff, for example a fixed UTC boundary, chosen only after checking rainfall data availability |
| FORECAST HORIZON | Daily/date-level target; not a claim of 24-hour onset precision |
| SPATIAL UNIT | Gauge-linked INDOFLOODS catchment |
| POSITIVE CLASS | A qualifying `Flood` or `Severe Flood` event according to a predeclared label rule; `Severe Flood` must not be treated as a universal physical severity scale |
| NEGATIVE CLASS | A gauge-day with no qualifying event, only where the underlying observation coverage confirms that absence is meaningful |
| STATIC FEATURES | Validated catchment area, relief, drainage, stream order, land cover, soil/lithology, DEM-derived terrain, and fixed administrative/exposure attributes |
| DYNAMIC FEATURES | Only rainfall, soil moisture, and continuous water-level/discharge values demonstrably available before the cutoff; T variables remain excluded until their operational timing is reproduced |
| AVAILABLE BEFORE PREDICTION | Pre-cutoff rainfall accumulations, antecedent moisture, prior observed levels/discharge, and fixed static features |
| POST-EVENT EXCLUDED | Peak level/discharge, peak dates, event volume, duration, recession, flood type, impacts, flooded area, and any feature calculated using data after the cutoff |

### Hypothetical row construction

For a hypothetical gauge-day cutoff, first identify the gauge-linked catchment and fixed static features. Then retrieve only rainfall and soil-moisture observations whose timestamps precede the cutoff, aggregate them using a documented window, and retrieve the contemporaneous water-level/discharge observations if an accessible series exists. Finally, assign the target from the event record only for the future date/window defined by the experiment. The example contains no invented values; it describes ordering and eligibility only.

## 9. Remaining Data Gaps

1. A recognized machine-readable Western Ghats boundary or a published, reproducible physiographic proxy.
2. Geometry repair review for 3 invalid catchments and investigation of 5 duplicate geometry groups.
3. Exact native spatial resolution and parameter definition for NASA POWER `GWETTOP`.
4. A fixed, versioned rainfall product and explicit UTC timestamp convention.
5. Timestamped continuous water-level/discharge observations aligned to open gauges, likely requiring CWC/India-WRIS access or another authoritative provider.
6. Confirmation that daily negative examples have adequate observation coverage.
7. Precise availability timing for ERA5/ERA5-Land or any retrospective rainfall/soil product used in an operational claim.
8. Administrative boundary files for catchment intersection and any village/ward display.
9. Village-level event or inundation labels if PRAVAH is to claim village-level prediction.
10. A leakage-safe mapping from event dates to prediction cutoffs and target dates.

## 10. Final Recommendation

- **Best current region:** Maharashtra Western Ghats proxy subset, pending boundary validation; Kerala remains a fallback.
- **Best flood-event source:** INDOFLOODS v1.0 for gauge/catchment event labels and static catchment context.
- **Best rainfall candidate:** NASA GPM IMERG for future sub-daily rainfall feasibility, with NASA POWER already demonstrating small timestamped point retrieval. Neither source fixes the missing event timestamps.
- **Best hydrological source:** an accessible timestamped CWC/India-WRIS or state-authority water-level/discharge series aligned to selected gauges. None is currently acquired.
- **Best soil-moisture candidate:** ERA5-Land or a carefully documented NASA POWER soil-wetness parameter as a coarse antecedent feature; not a local sensor substitute.
- **Defensible target now:** daily/date-level gauge-event analysis only.
- **True short-term flash-flood forecasting:** **not feasible with currently available data**.
- **Required before modelling:** obtain timestamped hydrological observations, finalize the physiographic boundary, repair/audit geometries, reproduce rainfall/soil availability timing, and define leakage-safe daily rows.

No ML pipeline, API, frontend, alert system, or simulated data should be implemented until these gaps are reviewed and the modelling target is approved.

## Sources Consulted

- [INDOFLOODS Zenodo record](https://zenodo.org/records/14584655)
- Local `variables_description_indofloods.pdf`, extracted to `data/metadata/variables_description_indofloods.txt`
- [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg)
- [NASA POWER hourly API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/)
- [ERA5-Land hourly dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land)
- [Central Water Commission hydrological data](https://www.cwc.gov.in/en/hydrological-data)
- [Central Water Commission flood forecasting and hydrological observation](https://www.cwc.gov.in/en/flood-forecasting-hydrological-observation)
