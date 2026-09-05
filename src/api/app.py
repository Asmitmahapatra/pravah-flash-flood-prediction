from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.schemas import (
    HealthResponse,
    HistoricalDateResponse,
    LivePredictionRequest,
    LivePredictionResponse,
    AlertRecord,
)
from src.inference.predictor import PravahInferenceEngine, clean_gauge_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pravah.api")

REPO_ROOT = Path(__file__).resolve().parents[2]
CATCHMENTS_GEOJSON = REPO_ROOT / "data" / "processed" / "target_catchments.geojson"
alerts: Dict[str, AlertRecord] = {}

# Instantiate engine singleton
engine = PravahInferenceEngine()

app = FastAPI(
    title="PRAVAH — Flash-Flood Early Warning API",
    description=(
        "REST API serving real-time 1-day ahead flash-flood risk inference, "
        "historical event simulation replay, and geospatial catchment intelligence "
        "for the Maharashtra Western Ghats."
    ),
    version="1.0.0",
)

# Enable CORS for web applications and dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
def get_health() -> HealthResponse:
    """Return system health, loaded models, and registered catchments count."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        project="PRAVAH Flash-Flood Prediction System",
        study_region="Maharashtra Western Ghats",
        available_models=engine.available_models,
        total_catchments=len(engine.registered_gauges),
    )


@app.get("/api/v1/catchments", tags=["Geospatial"])
def get_catchments_geojson() -> Any:
    """
    Return GeoJSON FeatureCollection of all 20 target Maharashtra Western Ghats catchments
    enriched with station names, river, danger levels, and operational bounds.
    """
    if not CATCHMENTS_GEOJSON.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target catchments GeoJSON file not found on disk."
        )

    with CATCHMENTS_GEOJSON.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Enrich features with station metadata
    for feature in data.get("features", []):
        gid = clean_gauge_id(feature.get("properties", {}).get("GaugeID", ""))
        info = engine.get_station_info(gid)
        feature["properties"].update(info)

    return data


@app.get("/api/v1/catchments/{gauge_id}", tags=["Geospatial"])
def get_single_catchment(gauge_id: str) -> Dict[str, Any]:
    """Retrieve station metadata and static characteristics for a single catchment."""
    gid = clean_gauge_id(gauge_id)
    if gid not in engine.registered_gauges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gauge '{gauge_id}' not found. Available gauges: {engine.registered_gauges}"
        )
    return engine.get_station_info(gid)


@app.post("/api/v1/predict/live", response_model=LivePredictionResponse, tags=["Inference"])
def predict_live_rainfall(request: LivePredictionRequest) -> LivePredictionResponse:
    """
    Predict 1-day ahead flood onset and active flood status given a 10-day daily rainfall sequence.
    """
    try:
        res = engine.predict_live(
            gauge_id=request.gauge_id,
            rainfall_history_10d=request.rainfall_history_10d,
            onset_model_name=request.onset_model or "RandomForest",
            active_model_name=request.active_model or "XGBoost",
        )
        response = LivePredictionResponse(status="success", **res)
        tier = response.alert_tier.tier
        if tier != "NORMAL":
            alert_id = (
                f"{response.station.gauge_id}:{tier}:"
                f"{response.task_a_onset['probability']:.4f}:"
                f"{response.task_b_active['probability']:.4f}"
            )
            if alert_id not in alerts:
                alerts[alert_id] = AlertRecord(
                    id=alert_id,
                    tier=tier,
                    gauge_id=response.station.gauge_id,
                    station_name=response.station.station_name,
                    probability=float(response.task_a_onset["probability"]),
                    active_probability=float(response.task_b_active["probability"]),
                    recommendation=response.alert_tier.recommendation,
                    created_at=datetime.now(timezone.utc),
                )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Live prediction error: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/api/v1/predict/historical/{date}", response_model=HistoricalDateResponse, tags=["Simulation"])
def predict_historical_date(
    date: str,
    onset_model: Optional[str] = Query("RandomForest", description="Onset model (RandomForest/XGBoost/LightGBM)"),
    active_model: Optional[str] = Query("XGBoost", description="Active model (XGBoost/LightGBM/RandomForest)"),
) -> HistoricalDateResponse:
    """
    Replay flood risk predictions across all catchments for any historical date in the observation record (1964–2020).
    """
    try:
        res = engine.predict_historical_date(
            date_str=date,
            onset_model_name=onset_model or "RandomForest",
            active_model_name=active_model or "XGBoost",
        )
        return HistoricalDateResponse(status="success", **res)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Historical simulation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get("/api/v1/models/summary", tags=["Models"])
def get_models_benchmark_summary() -> Dict[str, Any]:
    """Retrieve comprehensive Phase 3 performance benchmarks and top feature importances."""
    return engine.get_models_summary()


@app.get("/api/v1/alerts", response_model=List[AlertRecord], tags=["Alerts"])
def get_alerts(include_acknowledged: bool = Query(True)) -> List[AlertRecord]:
    """Return server-side risk alerts generated by live inference calls."""
    records = list(alerts.values())
    if not include_acknowledged:
        records = [record for record in records if not record.acknowledged]
    return sorted(records, key=lambda record: record.created_at, reverse=True)


@app.post("/api/v1/alerts/{alert_id}/acknowledge", response_model=AlertRecord, tags=["Alerts"])
def acknowledge_alert(alert_id: str) -> AlertRecord:
    """Mark one alert as acknowledged by an operator."""
    if alert_id not in alerts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alerts[alert_id] = alerts[alert_id].model_copy(update={"acknowledged": True})
    return alerts[alert_id]


@app.post("/api/v1/alerts/acknowledge-all", response_model=List[AlertRecord], tags=["Alerts"])
def acknowledge_all_alerts() -> List[AlertRecord]:
    """Acknowledge every alert currently held by the API process."""
    for alert_id, record in alerts.items():
        alerts[alert_id] = record.model_copy(update={"acknowledged": True})
    return get_alerts()
