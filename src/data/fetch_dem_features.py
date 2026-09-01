from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_GRID = REPO_ROOT / "data" / "processed" / "master_daily_grid_splits.parquet"


def main() -> None:
    print("PRAVAH does not use synthetic or deterministic proxy DEM formulas.")
    print("The project uses the verified static catchment descriptors already stored in:")
    print(MASTER_GRID)
    print("If you need genuine terrain data, fetch it externally from a real source such as OpenTopography or Open-Elevation and join it explicitly to the validated catchment table.")


if __name__ == "__main__":
    main()
