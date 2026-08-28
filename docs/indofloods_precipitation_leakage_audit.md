# INDOFLOODS Precipitation Leakage Audit

**Audit date:** 2026-08-28  
**Source files:** `precipitation_variables_indofloods.csv`, `variables_description_indofloods.pdf`, and the INDOFLOODS Zenodo record.  
**Decision:** Do not use `T1d`-`T10d` in a model until the prediction cutoff and rainfall-product version are explicitly reproduced.

## Verified Definition

The local PDF defines the event-scale precipitation fields as follows:

- **T1d:** daily precipitation one day before the flood start date.
- **T2d-T10d:** cumulative daily precipitation over the preceding 2, 3, 4, 5, 6, 7, 8, 9, and 10 days before the flood start date.
- **Units:** millimetres.
- **Rainfall source:** the corrected mean of **ERA5 daily precipitation probabilistic estimates**, at 0.1 degree spatial resolution, is used to derive event-scale precipitation over the catchments for all flood events. The PDF cites Tang et al. (2022).
- **Reference point:** the flood **start date**, not the peak date.
- **Temporal granularity:** daily accumulation. No hour, minute, timezone, product retrieval time, or operational latency is stored in the CSV.

The CSV contains 4,548 rows and only `EventID`, `T1d` through `T10d`. All 4,548 event IDs are unique and all T columns have 0 blank values. The CSV does not contain the event start date, accumulation-end timestamp, product version, or retrieval/availability timestamp.

## Per-Variable Classification

| Variable | Exact accumulation | Reference | Before/after event | Prediction-time assessment | Leakage classification |
|---|---|---|---|---|---|
| `T1d` | One daily precipitation value | One day before flood start date | Before documented flood start date | Potentially available before the event, but exact day boundary, timezone, ERA5 release/version, and operational availability are absent | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T2d` | Cumulative daily precipitation for 2 preceding days | Before flood start date | Before documented flood start date | Same issue; safe only if calculated with data available strictly before the prediction cutoff | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T3d` | Cumulative daily precipitation for 3 preceding days | Before flood start date | Before documented flood start date | Same issue | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T4d` | Cumulative daily precipitation for 4 preceding days | Before flood start date | Before documented flood start date | Same issue | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T5d` | Cumulative daily precipitation for 5 preceding days | Before flood start date | Before documented flood start date | Same issue | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T6d` | Cumulative daily precipitation for 6 preceding days | Before flood start date | Before documented flood start date | Same issue | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T7d` | Cumulative daily precipitation for 7 preceding days | Before flood start date | Before documented flood start date | Same issue | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T8d` | Cumulative daily precipitation for 8 preceding days | Before flood start date | Before documented flood start date | Same issue | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T9d` | Cumulative daily precipitation for 9 preceding days | Before flood start date | Before documented flood start date | Same issue | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |
| `T10d` | Cumulative daily precipitation for 10 preceding days | Before flood start date | Before documented flood start date | Same issue | **POTENTIALLY SAFE - REQUIRES ASSUMPTION** |

## Why They Are Not Yet `SAFE FOR PREDICTION`

The PDF establishes that the windows precede the recorded flood start **date**, which strongly argues against post-event leakage in the intended construction. It does not establish:

1. The exact daily accumulation boundary and timezone.
2. Whether the source is ERA5 or ERA5-Land; the PDF text says “Em-earth” in the product description, while the cited source and context need paper-level confirmation.
3. Which ERA5 product version and release was used.
4. Whether the values were generated retrospectively using a finalized/revised product.
5. Whether the complete preceding day was available operationally before the intended prediction time.
6. Whether any event-start date was assigned after observing a flood threshold crossing, creating a label/feature timing issue.

Therefore, use in a future modelling table requires a documented assumption such as: “At prediction time at 00:00 UTC on the flood-start date, only complete daily accumulations ending before that cutoff are used, from a fixed, versioned rainfall product.” Until the actual daily source and timing are reproduced, the fields remain potentially safe rather than safe.

## Leakage Rules for PRAVAH

- Exclude `T1d`-`T10d` from all modelling experiments until their computation is independently reproduced.
- Never use peak date, peak level, peak discharge, flood volume, event duration, time to peak, recession time, or flood type as an input for the same event.
- Do not use any variable whose accumulation window overlaps the flood start or peak unless the prediction time is explicitly later and the target is redefined accordingly.
- A retrospective feature can be valid for historical association but still invalid for an operational forecast if it was not available at the stated cutoff.
- Keep the rainfall source, product version, timestamp convention, retrieval time, and cutoff in every future training row.

## Audit Result

`T1d`-`T10d` are **pre-start-date antecedent rainfall variables by documented definition**, not post-event totals. They are not classified as `POST-EVENT / LEAKAGE` based on the PDF. However, because the CSV lacks the source version and availability timestamp, every T variable is classified **POTENTIALLY SAFE - REQUIRES ASSUMPTION**. They must not be used as model features until those assumptions are verified.

## References

- INDOFLOODS variables description PDF stored at `data/raw/indofloods/variables_description_indofloods.pdf` and extracted to `data/metadata/variables_description_indofloods.txt`.
- [INDOFLOODS Zenodo record](https://zenodo.org/records/14584655).
- [ERA5 hourly documentation](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels).
