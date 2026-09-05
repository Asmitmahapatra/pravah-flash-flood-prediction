from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LivePredictionRequest(BaseModel):
    gauge_id: str = Field(..., description="Target gauge ID (e.g. '684' or 'INDOFLOODS-gauge-684')", example="684")
    rainfall_history_10d: List[float] = Field(
        ...,
        min_items=10,
        max_items=10,
        description="10 daily rainfall amounts (mm) in chronological order: [P_{T-10}, ..., P_{T-1}]",
        example=[0.0, 2.5, 8.0, 15.2, 45.0, 92.5, 110.0, 35.0, 12.0, 28.4]
    )
    onset_model: Optional[str] = Field("RandomForest", description="Classifier for Onset (RandomForest / XGBoost / LightGBM)")
    active_model: Optional[str] = Field("XGBoost", description="Classifier for Active State (XGBoost / LightGBM / RandomForest)")


class StationInfoSchema(BaseModel):
    gauge_id: str
    full_gauge_id: str
    station_name: str
    river: str
    basin: str
    latitude: float
    longitude: float
    warning_level_m: float
    danger_level_m: float


class AlertTierSchema(BaseModel):
    tier: str
    color: str
    recommendation: str


class TaskPredictionSchema(BaseModel):
    model_used: str
    probability: float
    threshold: float
    is_positive_predicted: bool


class LivePredictionResponse(BaseModel):
    status: str = "success"
    station: StationInfoSchema
    alert_tier: AlertTierSchema
    task_a_onset: Dict[str, Any]
    task_b_active: Dict[str, Any]
    antecedent_rainfall_summary: Dict[str, Any]


class HistoricalCatchmentResult(BaseModel):
    gauge_id: str
    station_name: str
    river: str
    latitude: float
    longitude: float
    alert_tier: str
    alert_color: str
    onset_probability: float
    onset_predicted: bool
    actual_onset_observed: int
    active_probability: float
    active_predicted: bool
    actual_active_observed: int
    rain_1d_mm: float
    rain_3d_sum_mm: float
    rain_7d_sum_mm: float


class HistoricalDateResponse(BaseModel):
    status: str = "success"
    date: str
    total_stations_active: int
    emergency_count: int
    warning_count: int
    advisory_count: int
    normal_count: int
    catchments: List[HistoricalCatchmentResult]


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    project: str = "PRAVAH Flash-Flood Prediction System"
    study_region: str = "Maharashtra Western Ghats"
    available_models: List[str]
    total_catchments: int


class AlertRecord(BaseModel):
    id: str
    tier: str
    gauge_id: str
    station_name: str
    probability: float
    active_probability: float
    recommendation: str
    created_at: datetime
    acknowledged: bool = False
