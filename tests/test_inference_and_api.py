import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from src.api.app import app
from src.inference.predictor import (
    PravahInferenceEngine,
    compute_antecedent_features,
    determine_alert_tier,
)

ROOT = Path(__file__).resolve().parents[1]


class PravahInferenceAndApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = PravahInferenceEngine()
        cls.client = TestClient(app)

    def test_compute_antecedent_features_correctness(self):
        # 10 days of rainfall [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        rain_10d = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        feats = compute_antecedent_features(rain_10d)
        
        self.assertEqual(feats["rain_1d"], 10.0)
        self.assertEqual(feats["rain_2d_sum"], 19.0)
        self.assertEqual(feats["rain_3d_sum"], 27.0)
        self.assertEqual(feats["rain_5d_sum"], 40.0)
        self.assertEqual(feats["rain_7d_sum"], 49.0)
        self.assertEqual(feats["rain_10d_sum"], 55.0)
        self.assertEqual(feats["rain_3d_max"], 10.0)
        self.assertEqual(feats["rain_7d_max"], 10.0)
        self.assertEqual(feats["rain_dry_days_3d"], 0.0)
        self.assertEqual(feats["has_gpm_coverage"], 1)

    def test_determine_alert_tier_logic(self):
        # Low risk
        tier, color, _ = determine_alert_tier(0.01, 0.30, 0.05, 0.50)
        self.assertEqual(tier, "NORMAL")
        self.assertEqual(color, "GREEN")

        # Advisory
        tier, color, _ = determine_alert_tier(0.20, 0.30, 0.10, 0.50)
        self.assertEqual(tier, "ADVISORY")
        self.assertEqual(color, "YELLOW")

        # Warning
        tier, color, _ = determine_alert_tier(0.35, 0.30, 0.20, 0.50)
        self.assertEqual(tier, "WARNING")
        self.assertEqual(color, "ORANGE")

        # Emergency
        tier, color, _ = determine_alert_tier(0.50, 0.30, 0.60, 0.50)
        self.assertEqual(tier, "EMERGENCY")
        self.assertEqual(color, "RED")

    def test_engine_live_prediction_karad(self):
        # Gauge 684 = Karad on Krishna River
        dry_rain = [0.0] * 10
        res_dry = self.engine.predict_live("684", dry_rain)
        self.assertEqual(res_dry["station"]["gauge_id"], "684")
        self.assertEqual(res_dry["alert_tier"]["tier"], "NORMAL")
        self.assertFalse(res_dry["task_a_onset"]["is_flood_onset_predicted"])

        # Heavy monsoon scenario (120mm peak)
        monsoon_rain = [5.0, 12.0, 25.0, 40.0, 65.0, 80.0, 110.0, 140.0, 125.0, 95.0]
        res_wet = self.engine.predict_live("684", monsoon_rain)
        self.assertGreater(res_wet["task_a_onset"]["probability"], 0.05)
        self.assertIn(res_wet["alert_tier"]["tier"], ["ADVISORY", "WARNING", "EMERGENCY"])

    def test_engine_historical_simulation(self):
        # Maharashtra flood peak in August 2019
        sim = self.engine.predict_historical_date("2019-08-05")
        self.assertEqual(sim["date"], "2019-08-05")
        self.assertGreaterEqual(sim["total_stations_active"], 18)
        self.assertGreaterEqual(sim["warning_count"] + sim["emergency_count"] + sim["advisory_count"], 1)

    def test_api_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["total_catchments"], 20)
        self.assertGreaterEqual(len(data["available_models"]), 3)

    def test_api_catchments_endpoint(self):
        response = self.client.get("/api/v1/catchments")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(len(data["features"]), 20)
        first_feat = data["features"][0]
        self.assertIn("station_name", first_feat["properties"])
        self.assertIn("danger_level_m", first_feat["properties"])

    def test_api_single_catchment_endpoint(self):
        response = self.client.get("/api/v1/catchments/684")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["gauge_id"], "684")
        self.assertEqual(data["station_name"], "Karad")

    def test_api_live_prediction_endpoint(self):
        payload = {
            "gauge_id": "684",
            "rainfall_history_10d": [0.0, 5.0, 10.0, 15.0, 20.0, 30.0, 50.0, 80.0, 90.0, 75.0],
            "onset_model": "RandomForest",
            "active_model": "XGBoost"
        }
        response = self.client.post("/api/v1/predict/live", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("alert_tier", data)
        self.assertIn("probability", data["task_a_onset"])

    def test_api_historical_simulation_endpoint(self):
        response = self.client.get("/api/v1/predict/historical/2019-08-04")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["date"], "2019-08-04")
        self.assertGreater(len(data["catchments"]), 0)

    def test_api_models_summary_endpoint(self):
        response = self.client.get("/api/v1/models/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("task_a_onset", data)
        self.assertIn("task_b_active", data)

    def test_api_alert_lifecycle(self):
        payload = {
            "gauge_id": "684",
            "rainfall_history_10d": [5.0, 8.0, 12.0, 14.0, 18.0, 25.0, 30.0, 40.0, 52.0, 68.0],
            "onset_model": "RandomForest",
            "active_model": "XGBoost",
        }
        prediction = self.client.post("/api/v1/predict/live", json=payload)
        self.assertEqual(prediction.status_code, 200)
        self.assertNotEqual(prediction.json()["alert_tier"]["tier"], "NORMAL")

        alerts = self.client.get("/api/v1/alerts?include_acknowledged=false")
        self.assertEqual(alerts.status_code, 200)
        alert = next(item for item in alerts.json() if item["gauge_id"] == "684")

        acknowledged = self.client.post(f"/api/v1/alerts/{alert['id']}/acknowledge")
        self.assertEqual(acknowledged.status_code, 200)
        self.assertTrue(acknowledged.json()["acknowledged"])

        unread = self.client.get("/api/v1/alerts?include_acknowledged=false")
        self.assertEqual(unread.status_code, 200)
        self.assertNotIn(alert["id"], [item["id"] for item in unread.json()])


if __name__ == "__main__":
    unittest.main()
