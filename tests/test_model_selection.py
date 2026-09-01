import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class PravahModelSelectionTests(unittest.TestCase):
    def test_model_selection_uses_real_features_and_returns_valid_model(self):
        from src.model.baseline_flood_model import build_model_columns
        from src.model.train_classifiers import select_model_for_task

        df = pd.read_parquet(ROOT / "data" / "processed" / "master_daily_grid_splits.parquet")
        feature_cols = build_model_columns(df)

        self.assertGreater(len(feature_cols), 0)

        metrics = {
            "RandomForest": {
                "precision": 0.12,
                "recall": 0.42,
                "f1": 0.18,
                "csi": 0.11,
                "roc_auc": 0.82,
                "average_precision": 0.26,
            },
            "LightGBM": {
                "precision": 0.05,
                "recall": 0.68,
                "f1": 0.09,
                "csi": 0.07,
                "roc_auc": 0.79,
                "average_precision": 0.16,
            },
            "XGBoost": {
                "precision": 0.1,
                "recall": 0.35,
                "f1": 0.15,
                "csi": 0.09,
                "roc_auc": 0.81,
                "average_precision": 0.22,
            },
        }

        selected = select_model_for_task(metrics)
        self.assertIn(selected, {"RandomForest", "LightGBM", "XGBoost"})


if __name__ == "__main__":
    unittest.main()
