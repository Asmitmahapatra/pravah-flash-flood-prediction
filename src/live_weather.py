from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence, Tuple
from urllib import error, parse, request


OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


def extract_last_10_daily_precipitation(payload: Dict[str, Any]) -> List[float]:
    """Extract the most recent 10 daily precipitation totals from an Open-Meteo payload."""
    daily = payload.get("daily", {})
    values = daily.get("precipitation_sum", [])
    if not values:
        return [0.0] * 10

    cleaned = []
    for item in list(values)[-10:]:
        try:
            cleaned.append(float(item or 0.0))
        except (TypeError, ValueError):
            cleaned.append(0.0)

    if len(cleaned) < 10:
        cleaned = [0.0] * (10 - len(cleaned)) + cleaned
    return cleaned[:10]


def fetch_daily_precipitation(lat: float, lon: float, days: int = 10) -> List[float]:
    """Fetch the recent daily precipitation totals for a coordinate pair from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "timezone": "auto",
        "past_days": str(days),
        "forecast_days": "0",
    }
    url = f"{OPEN_METEO_BASE}?{parse.urlencode(params)}"
    with request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return extract_last_10_daily_precipitation(payload)


def get_live_rainfall_for_station(station_info: Dict[str, Any]) -> Tuple[List[float], Dict[str, str]]:
    """Look up a station's current recent precipitation from the live weather API."""
    lat = float(station_info.get("latitude", 0.0))
    lon = float(station_info.get("longitude", 0.0))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Station coordinates are invalid for live weather lookup.")

    values = fetch_daily_precipitation(lat, lon)
    meta = {
        "source": "Open-Meteo",
        "lat": str(lat),
        "lon": str(lon),
    }
    return values, meta
