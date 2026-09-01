from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_GRID = REPO_ROOT / "data" / "processed" / "master_daily_grid_splits.parquet"


def main() -> None:
    print("PRAVAH does not fabricate land-cover, population, or urban density proxies.")
    print("Use the validated physical descriptors already embedded in the processed dataset:")
    print(MASTER_GRID)
    print("For genuine land-cover or population layers, query a real STAC or Earth observation API and join the resulting values by GaugeID/geometry.")


if __name__ == "__main__":
    main()
