from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_GRID = REPO_ROOT / "data" / "processed" / "master_daily_grid_splits.parquet"


def main() -> None:
    print("PRAVAH does not generate synthetic OSM proxy infrastructure metrics.")
    print("The genuine infrastructure descriptors are already present in the validated catchment dataset (for example Road Density and Night Light).")
    print(MASTER_GRID)
    print("To fetch genuine OSM features, use the Overpass API directly and join real road/hospital counts to the validated catchment table.")


if __name__ == "__main__":
    main()
