import unittest
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PravahDashboardTests(unittest.TestCase):
    def test_dashboard_compiles(self):
        dash_path = ROOT / "src" / "dashboard" / "app.py"
        self.assertTrue(dash_path.exists())
        py_compile.compile(str(dash_path), doraise=True)


if __name__ == "__main__":
    unittest.main()
