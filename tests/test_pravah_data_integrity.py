import re
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class PravahDataIntegrityTests(unittest.TestCase):
    def test_processed_dataset_contains_real_feature_columns(self):
        df = __import__("pandas").read_parquet(ROOT / "data" / "processed" / "master_daily_grid_splits.parquet")
        self.assertEqual(df["GaugeID"].nunique(), 20)
        self.assertGreaterEqual(len([c for c in df.columns if c.startswith("rain_")]), 9)
        self.assertGreaterEqual(
            len([c for c in df.columns if c not in {"GaugeID", "Date", "split", "target_onset", "target_active", "target_peak"} and not c.startswith("rain_")]),
            100,
        )

    def test_no_proxy_or_synthetic_feature_formulas_remain(self):
        for file_path in [
            ROOT / "src" / "data" / "fetch_dem_features.py",
            ROOT / "src" / "data" / "fetch_osm_infrastructure.py",
            ROOT / "src" / "data" / "fetch_lulc_population.py",
        ]:
            text = file_path.read_text(encoding="utf-8")
            self.assertNotIn("540.0 + 18.0 * (lat - 16.0)", text)
            self.assertNotIn("deterministic fallback", text.lower())
            self.assertNotIn("proxy values", text.lower())

    def test_baseline_model_excludes_constant_and_null_features(self):
        from src.model.baseline_flood_model import build_model_columns

        df = pd.read_parquet(ROOT / "data" / "processed" / "master_daily_grid_splits.parquet")
        feature_cols = build_model_columns(df)
        self.assertGreater(len(feature_cols), 0)

        X = df[feature_cols]
        self.assertFalse(any(X[col].isna().all() for col in feature_cols))
        self.assertFalse(any(X[col].nunique(dropna=True) <= 1 for col in feature_cols))


if __name__ == "__main__":
    unittest.main()
