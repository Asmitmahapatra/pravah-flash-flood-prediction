from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURE_PATH = REPO_ROOT / "data" / "processed" / "target_catchment_spatial_features.csv"
TARGET_GAUGES = {
    "585", "589", "596", "602", "612", "626", "635", "640", "642", "643",
    "645", "646", "648", "654", "656", "668", "678", "681", "682", "684"
}


def validate() -> None:
    if not FEATURE_PATH.exists():
        raise FileNotFoundError(f"Missing feature file: {FEATURE_PATH}")

    df = pd.read_csv(FEATURE_PATH)
    if "GaugeID" not in df.columns:
        raise ValueError("Feature file does not contain a GaugeID column.")

    df["GaugeID"] = df["GaugeID"].astype(str)
    gauge_set = set(df["GaugeID"].unique())
    missing = sorted(TARGET_GAUGES - gauge_set)
    extra = sorted(gauge_set - TARGET_GAUGES)
    if missing or extra:
        raise AssertionError(f"Gauge mismatch. Missing={missing}; Extra={extra}")

    nan_count = int(df.isna().sum().sum())
    if nan_count != 0:
        raise AssertionError(f"Feature matrix contains {nan_count} missing values across all columns.")

    print(f"[VALIDATION] 20/20 target catchments present in {FEATURE_PATH}")
    print(f"[VALIDATION] Missing values: {nan_count}")
    print(f"[VALIDATION] Rows: {len(df)}")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    validate()
