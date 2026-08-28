# PRAVAH Phase 1: Dataset Inventory

**Status:** Documentation and compatibility inspection only  
**Inspection date:** 2026-08-28  
**Scope:** Candidate-source metadata, documentation, published file listings, and small-file schema previews. No bulk datasets were downloaded. No model, forecast horizon, case-study region, or prediction result is finalized.

## Reading This Report

- **Verified** means stated by the source documentation or visible in a published file preview.
- **Pending** means it requires downloading a small file or inspecting a sample locally.
- A source can support a task in principle while still being unsuitable for the final flash-flood target.
- `Yes` below means potentially useful, not scientifically validated for PRAVAH.

## Executive Finding

The best first flood source is **INDOFLOODS v1.0**, subject to a local audit of timestamps, missingness, duplicate keys, station coverage in hilly regions, and access status. It provides station-level flood events with dates, water level, discharge, duration, event type, station coordinates, warning/danger levels, and catchment attributes. It is an observational river-gauge event database, so it is more suitable for **gauge/catchment flood forecasting** than for direct village-level flash-flood prediction.

The IFI family is valuable for long historical coverage, district impacts, validation, and context, but its documented public files are primarily event/district records and do not by themselves establish a short-term forecasting target. The India Flood Atlas is useful for susceptibility/risk context and validation, but it is a simulated 10 km/sub-basin product and must not be presented as a short-term prediction label.

## Candidate Flood Datasets

| Dataset | Format and approximate size | Geographic and spatial coverage | Temporal coverage and resolution | Coordinates, timestamps, labels, impacts | Missingness, duplicates, CRS | Forecasting / susceptibility / risk / validation | Short-term flash-flood suitability |
|---|---|---|---|---|---|---|---|
| [India Flood Inventory - HydroSense Lab](https://github.com/hydrosenselab/India-Flood-Inventory) | Git repository containing shapefiles and versioned data directories; exact repository size and individual file sizes pending | India; repository describes an official national geospatial flood dataset. Exact geometry coverage pending sample audit | Versions include older IFI releases; current README points to Zenodo. Exact record dates depend on selected version | Fields not verified from README. Shapefile attributes and event date precision pending | CRS, nulls, duplicate geometry/record keys pending local inspection | Flood context, susceptibility/risk mapping, validation: potentially yes. Forecasting: not established | **No decision yet.** Do not use until event timestamp precision and target semantics are confirmed |
| [India Flood Inventory - Zenodo DOI](https://zenodo.org/doi/10.5281/zenodo.4742142) | Versioned Zenodo record; the DOI currently resolves to the newer 2025 record. Latest v4 files total about 1.9 MB | National India coverage; district names and LGD state/district codes are present in v4 supporting files | Latest v4 describes IMD-sourced events from 1967-2023. Event temporal resolution and exact date fields require full inventory schema audit | Latest v4 supporting files verified: district name, human fatality, injured, population, mean flood duration, flooded-area fields, and DFSI. Main inventory schema pending | Latest v4 license is CC BY-NC 4.0. CRS/coordinate fields, null counts, and duplicate keys pending main CSV audit | Flood history, risk mapping, validation: yes. Susceptibility: indirect. Short-term forecasting: not established | **No** for a near-real-time target without finer event timestamps and aligned dynamic observations |
| [India Flood Inventory + Impacts 1967-2023, Zenodo v3](https://zenodo.org/records/11275211) | CSV files, about 1.9 MB total: `India_Flood_Inventory_v3.csv` about 1.8 MB; impact/area files about 19-33 kB | National India; district-level impact and flooded-area tables | 1967-2023 according to record description. Temporal resolution of main event records pending full schema audit | Verified supporting fields: `Dist_Name`, `Human_fatality`, `Human_injured`, `Population`, `Mean_Flood_Duration`, `Percent_Flooded_Area`, `Permanent_Water`, corrected flooded area, and DFSI | CC BY 4.0 for v3. CRS/coordinates, null counts, and duplicate records in the main CSV pending audit | Flood history, risk mapping, validation: yes. Susceptibility: indirect. Forecasting: weak without hourly/sub-daily labels | **No** for short-term flash-flood prediction; useful as historical context and validation |
| [INDOFLOODS](https://zenodo.org/records/14584655) | CSV plus PDF and catchment shapefile ZIP, about 2.2 MB total: events 469.7 kB, precipitation variables 677.5 kB, catchments 664.8 kB, characteristics 146.7 kB, metadata 40.1 kB | India gauge/catchment network; published version excludes Ganga and Brahmaputra basins. Metadata includes station latitude/longitude, river, basin, state, and catchment | Flood events span station-specific periods, with examples from 1965-2020; start/end and peak dates are present. Events are generally daily/date-level, not hourly | Verified event fields: EventID, start/end date, peak flood level/date, peak discharge/date, flood volume, duration, time to peak, recession time, flood type. Metadata includes latitude/longitude and station levels. Labels include `Flood` and `Severe Flood` | CC BY 4.0. Source notes academic/research access and asks users to cite the dataset and original sources. Some stations are marked Open or Restricted. Missing hydrological values are visible in previews. Duplicate key, CRS of shapefiles, and exact null counts pending audit | Forecasting: **potentially yes** at gauge/catchment scale. Susceptibility: yes through catchment attributes. Risk mapping: potentially. Validation: yes | **Best candidate, but not yet proven.** It can support event classification or discharge/level forecasting only after leakage, availability, and spatial-transfer limitations are resolved. It is not direct village-level flood extent data |
| [India Flood Atlas](https://github.com/wcl-iitgn/india-flood-atlas-data) | JSON files in GitHub; exact repository size small but individual file sizes not documented in README | India; state, district, and sub-basin products | Reconstructed/simulated flood record for 1901-2020; underlying flooded-area simulation at 10 km; annual/long-term risk products in repository | Published JSON names include annual flood area/fraction, maximum area fraction, and state/district/sub-basin risk data. No verified event timestamp or local sensor label | CRS, nulls, duplicate keys, and licensing terms require repository/data inspection. README requests citation | Susceptibility/risk mapping: **yes**. Validation/context: potentially. Forecasting: no, unless used only as historical contextual covariates with careful provenance | **No** as a direct flash-flood forecast label; simulated long-term risk at 10 km/sub-basin scale |
| [HydroSense Lab datasets](https://hydrosense.iitd.ac.in/resources/) | Multiple linked datasets; formats and sizes vary and are pending per linked product | Varies. Resources include India and global products | Varies. IPED is described as daily 0.1-degree India precipitation; other products differ | Varies. The page identifies INDOFLOODS, IPED, landslide susceptibility, GloFlo, and other products, but schemas require source-specific inspection | Licensing varies by product and original source; do not infer one license for all resources | Rainfall, susceptibility, catchment attributes, and validation support depend on product | **Source catalogue, not one dataset.** Select only after product-level compatibility and licensing review |

## Environmental and Reference Sources

| Source | Verified resolution / coverage / temporal characteristics | Format and access | PRAVAH contribution | Main concern |
|---|---|---|---|---|
| [IMD daily gridded rainfall](https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html) | India grid from 6.5N, 66.5E to 38.5N, 100E; 0.25 x 0.25 degree; daily; 1901-2024 | NetCDF; official download page. Dataset is in millimetres and contains yearly 365/366-record files | Historical rainfall accumulation, climatology, event alignment, and validation | Daily and roughly 25 km grid cells are unlikely to resolve the onset of many flash floods. Access and redistribution conditions should be recorded from the current IMD terms |
| [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg) | Global precipitation estimates; half-hourly products updated for near-real-time use. IMERG record combines TRMM-era and GPM-era data and spans more than two decades | HDF5/NetCDF and value-added GeoTIFF options are documented; PPS access may require registration. Early, Late, and Final runs have different latency and quality | Best candidate for sub-daily rainfall features and near-real-time ingestion, subject to product/run selection | Satellite precipitation error in complex terrain, product revisions, latency, and coarse grid relative to village scale. Early/Final run must never be mixed without documentation |
| [ERA5 hourly single levels](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels) | Global; 0.25 degree reanalysis grid; hourly; 1940-present; updated daily with about 5-day latency | GRIB; Copernicus Climate Data Store; CC BY | Long historical hourly covariates, climatology, and gap/context analysis | Reanalysis is too coarse for hyper-local terrain rainfall and is not a timely operational observation because of latency |
| [NASA SRTMGL1 v3 DEM](https://www.earthdata.nasa.gov/data/catalog/lpcloud-srtmgl1-003) | Global land from 60N to 56S; about 30 m; acquisition in February 2000; HGT tiles, about 7 MB each | HGT and NetCDF4 variants; NASA Earthdata access; openly shared with citation guidance | Elevation, slope, aspect, relief, drainage derivation, terrain context | One historical acquisition, void-fill provenance, tile management, and DEM-derived flow paths need validation in steep terrain |
| [HydroSHEDS core layers](https://www.hydrosheds.org/products/hydrosheds) / [HydroRIVERS](https://www.hydrosheds.org/products/hydrorivers) | HydroSHEDS core layers at 3, 15, 30 arc-sec and coarser products; HydroRIVERS is a global vector network derived from 15 arc-sec layers and generally includes rivers with catchment area at least 10 km2 or average flow at least 0.1 m3/s | Raster and vector downloads; Asia HydroRIVERS is documented at about 91 MB shapefile or 103 MB geodatabase. HydroSHEDS license and attribution apply | Drainage direction, flow accumulation, basin delineation, river proximity, and catchment linkage | Small streams and local drainage may be absent. HydroRIVERS is not a substitute for local authoritative drainage data |
| [geoBoundaries](https://www.geoboundaries.org/) | Country administrative boundary database, with levels varying by country and release | Common GIS formats; CC BY 4.0; acknowledgement required | Reproducible state/district/sub-district map boundaries and spatial joins | Village/ward coverage and Indian boundary version must be verified. Boundary dates may not match flood inventory LGD codes |
| [OpenStreetMap](https://www.openstreetmap.org/about) | Global volunteered geographic data; feature completeness varies locally and changes over time | OSM data and services; attribution required; ODbL applies to data use | Roads, buildings, waterways, bridges, facilities, and evacuation context | Not a uniform authoritative administrative source; extract date, completeness, and licensing obligations must be documented |
| Copernicus global Soil Water Index | Global SWI documented at 12.5 km; 2007-present. European surface soil moisture is documented at 1 km, while global SWI is the relevant India-scale option | Copernicus Land Monitoring Service access; product-specific data policy applies | Antecedent wetness feature and hydrological context | 12.5 km is coarse for village-level use; depth/representativeness, missingness, and release latency require sample inspection |
| ESA CCI soil moisture | Candidate global soil-moisture family; current service metadata was not reliably available during this pass | Product-level download and licence details pending | Possible long historical antecedent-moisture feature | Do not select until current product version, resolution, temporal sampling, and India coverage are verified |
| Local streamflow / soil sensors | No project data supplied or verified | Must be obtained from an authority, published archive, or later clearly labelled test interface | Direct hydrological response and future real-time ingestion | Availability, privacy, calibration, and station access may prevent use. No simulated sensor data in Phase 1 |

## Required Field Inventory

The following fields are available or pending based on source documentation and small previews:

| Required field | Current status |
|---|---|
| Dataset name and source URL | Verified above |
| File format and approximate file size | Verified where the source publishes it; repository/sample sizes remain pending where undocumented |
| Geographic coverage | Verified at product level for most sources; exact selected-record coverage pending local audit |
| Spatial resolution | Verified for gridded/raster products; event inventories are station, district, catchment, or sub-basin rather than a uniform pixel resolution |
| Temporal coverage and resolution | Verified at product level where documented; exact IFI field precision and station-level INDOFLOODS gaps pending |
| Coordinates/geographic fields | INDOFLOODS station metadata has latitude/longitude; IFI main inventory and Atlas geographic fields pending schema audit |
| Timestamps | INDOFLOODS has start/end/peak dates; IFI and Atlas timestamp precision pending |
| Flood/event labels | INDOFLOODS has `Flood` and `Severe Flood`; IFI label semantics pending main inventory schema; Atlas is simulated flood/risk data |
| Severity/impact | INDOFLOODS has levels, discharge, volume, duration, and event type; IFI has fatalities, injuries, population, duration, flooded area, and DFSI |
| Missing values | Visible in INDOFLOODS previews for several discharge/volume fields; exact rates pending local profiling |
| Duplicate records | Not reliably determinable without downloading and profiling the selected files |
| CRS | Raster/product coordinate systems are documented for SRTM and gridded products; inventory and catchment shapefile CRS pending local inspection |
| Licensing/usage restrictions | Product-specific licenses and attribution requirements are recorded above; station `Restricted` status in INDOFLOODS needs access-policy review |

## Compatibility Assessment

### Recommended primary sources

1. **INDOFLOODS v1.0** for the first event-target compatibility audit and possible gauge/catchment forecasting prototype.
2. **GPM IMERG** for sub-daily rainfall candidate features, with the run and version recorded explicitly.
3. **SRTMGL1 v3** for terrain features.
4. **geoBoundaries**, supplemented by authoritative Indian boundaries if village/ward display is required.
5. **Copernicus global Soil Water Index**, only as an antecedent-moisture candidate after evaluating its coarse spatial scale and missingness.

### Secondary and validation sources

- **IFI v3/v4:** historical district event and impact context, case-study screening, and external validation. Do not treat DFSI or flooded-area percentages as short-term predictions.
- **India Flood Atlas:** long-term simulated risk/susceptibility context and coarse validation only.
- **HydroSHEDS/HydroRIVERS:** derived drainage and catchment features; local authoritative hydrography should take precedence where available.
- **IMD daily rainfall:** historical baseline and climatology; not the preferred short-term input unless sub-daily data cannot be obtained.
- **ERA5:** historical hourly context and gap analysis; not the preferred real-time rainfall source.

## Candidate Case-Study Regions

These are **initial screening candidates, not final selections**:

1. **Kerala Western Ghats:** INDOFLOODS contains multiple open stations in Kerala, including rivers in the west-flowing basin group; the region is hilly and has strong rainfall relevance. Local flash-flood labels, village boundaries, and rainfall/sensor overlap must still be verified.
2. **Maharashtra Western Ghats:** INDOFLOODS contains multiple open Maharashtra stations and catchments, while SRTM, GPM, boundaries, and drainage layers are available in principle. The final subregion must be selected after checking event density and terrain/rainfall overlap.
3. **Uttarakhand:** hilly and directly relevant to the SIH context, with historical IFI coverage and some INDOFLOODS stations in the Ganga system. Several INDOFLOODS stations are restricted and the published version excludes the Ganga basin, so this option depends on obtaining usable alternative streamflow/event data.

We should select one region only after measuring spatial overlap, event count, open-data access, label precision, and rainfall availability. No nationwide village-level claim is justified at this stage.

## Main Compatibility Problems

1. **Event definition mismatch:** IFI, INDOFLOODS, and the Flood Atlas represent different phenomena and observation/simulation processes.
2. **Spatial mismatch:** village/ward output is finer than IMD, GPM, ERA5, soil-moisture, and many flood products. Model units should initially be gauge catchments or a defensible grid, then be aggregated for display.
3. **Temporal mismatch:** INDOFLOODS events are date-level in published previews, while GPM is sub-daily and ERA5 hourly. This may prevent a defensible next-hours flash-flood label.
4. **Gauge versus areal flooding:** INDOFLOODS detects threshold exceedance at gauges; it does not directly label every flooded village or inundated pixel.
5. **Restricted data:** many INDOFLOODS stations are marked `Restricted`; the public package also excludes Ganga and Brahmaputra basins.
6. **Missing hydrology:** discharge and volume are blank for some events, especially newer or restricted stations.
7. **Boundary incompatibility:** historical district names, LGD codes, current administrative boundaries, and OSM/geoBoundaries geometries may not join cleanly.
8. **Terrain rainfall error:** satellite and reanalysis products can be biased in steep terrain and may not represent local convective rainfall.
9. **Leakage risk:** INDOFLOODS includes event-scale precipitation and catchment attributes. Those fields must be separated into available-at-prediction-time versus post-event-derived variables before modelling.
10. **Insufficient flash-flood labels:** if no source provides sub-daily event onset or areal inundation labels, the scientifically honest first target may be gauge flood-event prediction or catchment flood-risk estimation rather than village-level flash-flood prediction.
11. **License and redistribution:** IFI v4 is CC BY-NC 4.0, while v3 and INDOFLOODS are CC BY 4.0. Third-party source terms remain applicable to derived catchment variables.

## What to Download Next

Download only these small, targeted assets first:

1. INDOFLOODS `metadata_indofloods.csv`, `floodevents_indofloods.csv`, `catchment_characteristics_indofloods.csv`, `precipitation_variables_indofloods.csv`, the variables-description PDF, and the catchment shapefile ZIP.
2. IFI v3 `India_Flood_Inventory_v3.csv` and its three small supporting CSVs. Also compare the v4 main CSV metadata and license before choosing a version.
3. India Flood Atlas JSON files only for a few candidate regions or one product at a time; do not download unrelated global assets.
4. A small GPM IMERG sample covering one candidate region and a limited historical period, using one documented run/version.
5. A limited ERA5 hourly rainfall sample for the same dates and region, for comparison rather than bulk ingestion.
6. SRTM tiles covering candidate-region bounding boxes only.
7. Administrative boundaries at state, district, and sub-district/village level for the same candidates, with source version and date recorded.
8. Asia HydroRIVERS or clipped HydroRIVERS/HydroSHEDS extracts only after a candidate region is shortlisted.
9. A small Copernicus SWI sample for the same region and period.

The next deliverable after these downloads should be a reproducible **local data-quality report** containing exact row counts, column names, dtypes, coordinate ranges, CRS, timestamp ranges, null counts, duplicate-key analysis, and cross-source spatial/temporal overlap. It should still precede target construction and model training.

## Recommendation Summary

**A. Recommended primary flood dataset:** INDOFLOODS v1.0, conditional on access and local quality audit. Use it initially for gauge/catchment event compatibility, not as proven village-level flash-flood labels.

**B. Recommended rainfall dataset:** NASA GPM IMERG for the short-term candidate because it provides half-hourly near-real-time products. Use IMD daily rainfall for long historical context and ERA5 for historical hourly comparison, not as an assumed operational source.

**C. Recommended DEM source:** NASA SRTMGL1 v3 at approximately 30 m, clipped to the selected case-study region.

**D. Recommended soil-moisture/hydrological source:** First preference is an accessible streamflow series aligned to INDOFLOODS stations. If that is unavailable, evaluate Copernicus global Soil Water Index as a coarse antecedent-moisture feature. Do not claim local soil-moisture sensing until actual sensor data is obtained.

**E. Recommended administrative boundary source:** geoBoundaries CC BY 4.0 for reproducible initial analysis, cross-checked against an authoritative Indian boundary source before village/ward publication.

**F. Recommended initial case-study regions:** Kerala Western Ghats, Maharashtra Western Ghats, and Uttarakhand as a conditional third candidate. These are screening candidates only.

**G. Main compatibility problems:** incompatible flood definitions, gauge versus areal labels, coarse environmental grids, date-level event timing, restricted stations, missing hydrology, boundary changes, terrain rainfall error, and possible post-event leakage in derived variables.

**H. What data we need to download next:** the small INDOFLOODS and IFI packages, limited same-region GPM/ERA5/SWI samples, SRTM tiles, candidate administrative boundaries, and clipped drainage data. No bulk national archive or model artifact is needed yet.

## Sources Consulted

- HydroSense Lab India Flood Inventory GitHub repository and README
- Zenodo records `10.5281/zenodo.4742142`, `10.5281/zenodo.11275211`, and `10.5281/zenodo.14584655`, including published file listings and small CSV previews
- India Flood Atlas GitHub README and data file listing
- IMD 0.25-degree daily gridded rainfall page
- NASA GPM IMERG and GPM data-directory pages
- Copernicus ERA5 hourly single-level dataset page
- NASA SRTMGL1 v3 Earthdata catalogue page
- HydroSHEDS and HydroRIVERS product pages
- geoBoundaries and OpenStreetMap documentation
- Copernicus Land Monitoring Service soil-moisture page
