import unittest
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PravahDashboardTests(unittest.TestCase):
    def test_dashboard_compiles(self):
        dash_path = ROOT / "src" / "dashboard" / "app.py"
        self.assertTrue(dash_path.exists())
        py_compile.compile(str(dash_path), doraise=True)

    def test_rainfall_validation_rules(self):
        from src.dashboard.app import validate_rainfall_inputs

        self.assertTrue(validate_rainfall_inputs(10.0, 20.0, 35.0))
        self.assertRaises(ValueError, validate_rainfall_inputs, -1.0, 20.0, 35.0)
        self.assertRaises(ValueError, validate_rainfall_inputs, 60.0, 50.0, 80.0)
        self.assertRaises(ValueError, validate_rainfall_inputs, 300.0, 400.0, 500.0)


if __name__ == "__main__":
    unittest.main()
