from __future__ import annotations

import base64
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.inference.predictor import PravahInferenceEngine, clean_gauge_id
from src.live_weather import get_live_rainfall_for_station

st.set_page_config(
    page_title="PRAVAH — Flash-Flood Early Warning Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGO_PATH = REPO_ROOT / "src" / "dashboard" / "assets" / "pravah_logo.svg"
ALERT_COLOR_MAP = {
    "NORMAL": "#2ecc71",
    "ADVISORY": "#f1c40f",
    "WARNING": "#e67e22",
    "EMERGENCY": "#e74c3c",
}
ALERT_EMOJI_MAP = {
    "NORMAL": "🟢 Normal",
    "ADVISORY": "🟡 Advisory",
    "WARNING": "🟠 Warning",
    "EMERGENCY": "🔴 Emergency",
}
RISK_ORDER = ["EMERGENCY", "WARNING", "ADVISORY", "NORMAL"]
PRESET_MAP = {
    "Lull": {"one_day": 5.0, "three_day": 15.0, "seven_day": 30.0},
    "Moderate": {"one_day": 35.0, "three_day": 80.0, "seven_day": 140.0},
    "Heavy": {"one_day": 90.0, "three_day": 180.0, "seven_day": 340.0},
    "Cloudburst": {"one_day": 220.0, "three_day": 420.0, "seven_day": 750.0},
}


@st.cache_resource
def get_inference_engine() -> PravahInferenceEngine:
    return PravahInferenceEngine()


@st.cache_data
def get_catchments_geojson() -> Dict[str, Any]:
    path = REPO_ROOT / "data" / "processed" / "target_catchments.geojson"
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_logo_html(width: int = 220) -> str:
    if LOGO_PATH.exists():
        svg_code = LOGO_PATH.read_text(encoding="utf-8")
        b64 = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
        return f'<img src="data:image/svg+xml;base64,{b64}" width="{width}px" style="margin-bottom: 10px;" />'
    return "<h2>🌊 PRAVAH</h2>"


def validate_rainfall_inputs(one_day: float, three_day: float, seven_day: float) -> bool:
    values = [float(one_day), float(three_day), float(seven_day)]
    if any(np.isnan(v) or np.isinf(v) for v in values):
        raise ValueError("Rainfall values must be finite numbers.")
    if any(v < 0 for v in values):
        raise ValueError("Rainfall values cannot be negative.")
    if values[0] > 250.0:
        raise ValueError("1-day rainfall cannot exceed 250 mm in the validated scenario range.")
    if values[1] > 500.0:
        raise ValueError("3-day rainfall cannot exceed 500 mm in the validated scenario range.")
    if any(v > 1000 for v in values):
        raise ValueError("Rainfall values cannot exceed 1000 mm.")
    if values[0] > values[1]:
        raise ValueError("1-day rainfall must be less than or equal to 3-day rainfall.")
    if values[1] > values[2]:
        raise ValueError("3-day rainfall must be less than or equal to 7-day rainfall.")
    return True


def build_10d_history_from_totals(one_day: float, three_day: float, seven_day: float) -> List[float]:
    validate_rainfall_inputs(one_day, three_day, seven_day)
    one_day = float(one_day)
    three_day = float(three_day)
    seven_day = float(seven_day)

    history = [0.0] * 10
    history[-1] = one_day

    remaining_3 = max(0.0, three_day - one_day)
    remaining_7 = max(0.0, seven_day - three_day)
    if remaining_3 > 0:
        history[-2] = remaining_3 * 0.6
        history[-3] = remaining_3 - history[-2]
    if remaining_7 > 0:
        spread = remaining_7 / 7.0
        for idx in range(7):
            history[-7 + idx] += spread

    if sum(history[-7:]) < seven_day:
        history[-7] += (seven_day - sum(history[-7:]))
    return [round(float(v), 3) for v in history]


def get_station_search_fields(gauge_id: str) -> Dict[str, str]:
    info = engine.get_station_info(gauge_id)
    district = "Unknown"
    meta_path = REPO_ROOT / "data" / "processed" / "target_metadata.csv"
    if meta_path.exists():
        meta_df = pd.read_csv(meta_path)
        row = meta_df[meta_df["GaugeID"].map(clean_gauge_id) == clean_gauge_id(gauge_id)]
        if not row.empty:
            district = str(row.iloc[0].get("District", "Unknown"))
    return {
        "station_name": str(info.get("station_name", "Unknown")),
        "gauge_id": str(gauge_id),
        "river": str(info.get("river", "Unknown")),
        "basin": str(info.get("basin", "Unknown")),
        "district": district,
    }


def station_label(gauge_id: str) -> str:
    info = engine.get_station_info(gauge_id)
    return f"{gauge_id} — {info.get('station_name', 'Unknown')}"


def build_live_map(selected_gauge: str, rainfall_history: List[float], onset_model: str, active_model: str):
    m = folium.Map(location=[18.3, 74.3], zoom_start=7.5, tiles="CartoDB Positron", control_scale=True)
    risk_by_gauge: Dict[str, str] = {}
    for gauge in engine.registered_gauges:
        result = engine.predict_live(
            gauge_id=gauge,
            rainfall_history_10d=rainfall_history,
            onset_model_name=onset_model,
            active_model_name=active_model,
        )
        risk_by_gauge[gauge] = result["alert_tier"]["tier"]

    for feature in geojson_data.get("features", []):
        gid = clean_gauge_id(feature.get("properties", {}).get("GaugeID", ""))
        info = engine.get_station_info(gid)
        tier = risk_by_gauge.get(gid, "NORMAL")
        is_selected = clean_gauge_id(gid) == clean_gauge_id(selected_gauge)
        fill_color = ALERT_COLOR_MAP.get(tier, "#2ecc71")

        folium.GeoJson(
            feature,
            style_function=lambda x, selected=is_selected, color=fill_color: {
                "fillColor": color,
                "color": "#1b2430",
                "weight": 3 if selected else 1.4,
                "fillOpacity": 0.75 if selected else 0.45,
            },
            tooltip=(
                f"<b>{info.get('station_name', 'Unknown')}</b><br>"
                f"Gauge: {gid}<br>"
                f"River: {info.get('river', 'Unknown')}<br>"
                f"District: {get_station_search_fields(gid).get('district', 'Unknown')}<br>"
                f"Tier: {tier}"
            ),
        ).add_to(m)

        lat = float(info.get("latitude", 0.0))
        lon = float(info.get("longitude", 0.0))
        if lat and lon:
            folium.CircleMarker(
                location=[lat, lon],
                radius=10 if is_selected else 7,
                color="#ffffff" if not is_selected else "#111827",
                weight=2,
                fill=True,
                fill_color=fill_color,
                fill_opacity=1,
                popup=(
                    f"<b>{info.get('station_name', 'Unknown')}</b><br>"
                    f"Gauge: {gid}<br>"
                    f"River: {info.get('river', 'Unknown')}<br>"
                    f"Tier: {tier}"
                ),
            ).add_to(m)
            if tier in ["WARNING", "EMERGENCY"]:
                folium.Circle(
                    location=[lat, lon],
                    radius=3800 if tier == "EMERGENCY" else 2400,
                    color=fill_color,
                    fill=True,
                    fill_opacity=0.12,
                    weight=1,
                ).add_to(m)
    return m


engine = get_inference_engine()
geojson_data = get_catchments_geojson()

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

with st.sidebar:
    st.markdown(get_logo_html(width=220), unsafe_allow_html=True)
    st.markdown("### ⚙️ Navigation & Controls")
    selected_view = st.radio(
        "Select View",
        [
            "🗺️ Live Risk & Catchment Map",
            "⏳ Historical Simulation Replay",
            "📊 Model Benchmarks & Explainability",
            "🛰️ Catchment Geospatial Telemetry",
        ],
    )

    st.divider()
    st.markdown("### 📍 Catchment Controls")
    search_term = st.text_input("Search by station name, gauge ID, river, basin, or district")
    gauge_options = engine.registered_gauges
    if search_term:
        needle = search_term.lower()
        gauge_options = [
            gauge for gauge in gauge_options
            if any(needle in value.lower() for value in get_station_search_fields(gauge).values())
        ]
    if not gauge_options:
        gauge_options = engine.registered_gauges
    selected_gauge = st.selectbox("Station / Catchment", gauge_options, format_func=station_label, index=0)
    risk_filter = st.selectbox("Risk-tier filter", ["ALL", "EMERGENCY", "WARNING", "ADVISORY", "NORMAL"])
    selected_date = st.date_input("Historical date", value=datetime(2019, 8, 5).date())

    st.divider()
    st.markdown("### 🌧️ Manual Rainfall Inputs")
    rainfall_mode = st.radio("Mode", ["Manual Simulation", "Live Weather"], index=0)
    one_day = st.number_input("1-day rainfall (mm)", min_value=0.0, max_value=1000.0, value=35.0, step=1.0)
    three_day = st.number_input("3-day cumulative (mm)", min_value=0.0, max_value=1000.0, value=80.0, step=1.0)
    seven_day = st.number_input("7-day cumulative (mm)", min_value=0.0, max_value=1000.0, value=140.0, step=1.0)
    preset_name = st.selectbox("Preset", ["Custom", *list(PRESET_MAP.keys())])
    if preset_name != "Custom":
        preset = PRESET_MAP[preset_name]
        one_day = preset["one_day"]
        three_day = preset["three_day"]
        seven_day = preset["seven_day"]

    st.divider()
    st.markdown("### 🤖 Active ML Models")
    onset_model = st.selectbox("Onset Classifier", ["RandomForest", "XGBoost", "LightGBM"], index=0)
    active_model = st.selectbox("Active State Classifier", ["XGBoost", "LightGBM", "RandomForest"], index=0)

    st.divider()
    st.info("📍 **Domain:** 20 open gauge stations across the Maharashtra Western Ghats catchment corridor.")
    if st.button("Refresh telemetry"):
        st.session_state.last_refresh = datetime.now()

header_col_1, header_col_2, header_col_3 = st.columns([1, 4, 2])
with header_col_1:
    st.markdown(get_logo_html(width=160), unsafe_allow_html=True)
with header_col_2:
    st.title("PRAVAH — Early Warning & Geospatial Intelligence System")
    st.caption("AI-driven flash-flood monitoring for Maharashtra Western Ghats catchments")
with header_col_3:
    st.markdown(f"**Current time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown(f"**Last refresh:** {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown(f"**Backend status:** ✅ Ready | models loaded: {len(engine.available_models)}")

st.divider()

try:
    validate_rainfall_inputs(one_day, three_day, seven_day)
    rainfall_history = build_10d_history_from_totals(one_day, three_day, seven_day)
    if rainfall_mode == "Live Weather":
        station_info = engine.get_station_info(selected_gauge)
        try:
            rainfall_history, weather_meta = get_live_rainfall_for_station(station_info)
            st.info(f"Live data source: {weather_meta.get('source', 'Open-Meteo')} | station {station_info.get('station_name', 'Unknown')}")
        except Exception as exc:
            st.warning(f"Live weather unavailable: {exc}. Falling back to manual rainfall values.")
    live_prediction = engine.predict_live(
        gauge_id=selected_gauge,
        rainfall_history_10d=rainfall_history,
        onset_model_name=onset_model,
        active_model_name=active_model,
    )
except Exception as exc:
    live_prediction = None
    st.warning(f"Validation / forecast error: {exc}")

count_cols = st.columns(4)
risk_counts = {tier: 0 for tier in RISK_ORDER}
if live_prediction is not None:
    for gauge in engine.registered_gauges:
        result = engine.predict_live(
            gauge_id=gauge,
            rainfall_history_10d=rainfall_history,
            onset_model_name=onset_model,
            active_model_name=active_model,
        )
        risk_counts[result["alert_tier"]["tier"]] = risk_counts.get(result["alert_tier"]["tier"], 0) + 1
for idx, tier in enumerate(RISK_ORDER):
    count_cols[idx].metric(f"{ALERT_EMOJI_MAP[tier]}", risk_counts.get(tier, 0))

if live_prediction is not None:
    station_info = engine.get_station_info(selected_gauge)
    current_tier = live_prediction["alert_tier"]["tier"]
    current_prob = live_prediction["task_a_onset"]["probability"]
    banner_style = ALERT_COLOR_MAP.get(current_tier, "#2ecc71")
    st.markdown(
        f"<div style='padding:14px 16px; border-radius:12px; background:{banner_style}; color:white; font-weight:600;'>"
        f"{ALERT_EMOJI_MAP.get(current_tier, current_tier)} {current_tier} | Probability {current_prob:.1%} | Station {station_info.get('station_name')} | Basin {station_info.get('basin')} | Issued {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data quality: validated"
        f"</div>",
        unsafe_allow_html=True,
    )
    if current_tier == "EMERGENCY":
        st.warning("Emergency: evacuation and immediate response guidance are active for this catchment.")
    elif current_tier == "WARNING":
        st.warning("Warning: inundation watch and emergency preparation should be initiated.")
    elif current_tier == "ADVISORY":
        st.info("Advisory: increased monitoring is recommended for this station.")
    else:
        st.success("Normal: routine surveillance is sufficient for the current forecast.")

    st.download_button(
        label="Download advisory summary",
        data=(
            f"PRAVAH advisory summary\n"
            f"Station: {station_info.get('station_name')}\n"
            f"Gauge ID: {selected_gauge}\n"
            f"Basin: {station_info.get('basin')}\n"
            f"Risk tier: {current_tier}\n"
            f"Probability: {current_prob:.1%}\n"
            f"Issued: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        ),
        file_name=f"pravah_advisory_{selected_gauge}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )

if selected_view == "🗺️ Live Risk & Catchment Map":
    st.subheader("🗺️ Live Catchment Risk Map & Rainfall Scenario Simulator")
    if live_prediction is None:
        st.info("Please correct the rainfall values to proceed with ML inference.")
    else:
        map_col, detail_col = st.columns([1.6, 1.2])
        with map_col:
            live_map = build_live_map(selected_gauge, rainfall_history, onset_model, active_model)
            components.html(live_map.get_root().render(), height=620, scrolling=False)
        with detail_col:
            info = engine.get_station_info(selected_gauge)
            st.markdown(f"### {info.get('station_name')} ({selected_gauge})")
            st.metric("Flood probability", f"{live_prediction['task_a_onset']['probability']:.1%}")
            st.metric("Risk tier", live_prediction["alert_tier"]["tier"])
            st.markdown(f"**Onset model used:** {live_prediction['task_a_onset']['model_used']}")
            st.markdown(f"**Active model used:** {live_prediction['task_b_active']['model_used']}")
            st.markdown(f"**Model thresholds:** onset {live_prediction['task_a_onset']['threshold']:.4f}; active {live_prediction['task_b_active']['threshold']:.4f}")
            st.markdown(f"**Rainfall summary:** 1d {live_prediction['antecedent_rainfall_summary']['rain_1d_mm']} mm | 3d {live_prediction['antecedent_rainfall_summary']['rain_3d_sum_mm']} mm | 7d {live_prediction['antecedent_rainfall_summary']['rain_7d_sum_mm']} mm | 10d {live_prediction['antecedent_rainfall_summary']['rain_10d_sum_mm']} mm")
            st.markdown(f"**Recommendation:** {live_prediction['alert_tier']['recommendation']}")
            st.markdown(f"**Coordinates:** {info.get('latitude')}°, {info.get('longitude')}°")
            st.markdown(f"**Warning stage:** {info.get('warning_level_m', 0.0)} m")
            st.markdown(f"**Danger stage:** {info.get('danger_level_m', 0.0)} m")

        fig = go.Figure()
        fig.add_trace(go.Bar(x=[f"T-{10-i}" for i in range(10)], y=rainfall_history, name="Rainfall", marker_color="#4f8ef7"))
        fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="threshold")
        fig.update_layout(title="Rainfall analytics", xaxis_title="Days prior", yaxis_title="Rainfall (mm)")
        st.plotly_chart(fig, use_container_width=True)

elif selected_view == "⏳ Historical Simulation Replay":
    st.subheader("⏳ Historical Flood Event Replay")
    historical_result = engine.predict_historical_date(str(selected_date), onset_model_name=onset_model, active_model_name=active_model)
    historical_df = pd.DataFrame(historical_result["catchments"])
    if risk_filter != "ALL":
        historical_df = historical_df[historical_df["alert_tier"] == risk_filter]
    st.markdown(f"### {selected_date} summary")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Active gauges", historical_result["total_stations_active"])
    k2.metric("Emergency", historical_result["emergency_count"])
    k3.metric("Warning", historical_result["warning_count"])
    k4.metric("Advisory", historical_result["advisory_count"])
    st.dataframe(
        historical_df[["gauge_id", "station_name", "river", "alert_tier", "onset_probability", "active_probability", "rain_1d_mm", "rain_3d_sum_mm", "rain_7d_sum_mm", "actual_onset_observed", "actual_active_observed"]].rename(columns={
            "gauge_id": "Gauge ID",
            "station_name": "Station",
            "river": "River",
            "alert_tier": "Risk tier",
            "onset_probability": "Onset prob",
            "active_probability": "Active prob",
            "rain_1d_mm": "1d (mm)",
            "rain_3d_sum_mm": "3d (mm)",
            "rain_7d_sum_mm": "7d (mm)",
            "actual_onset_observed": "Observed onset",
            "actual_active_observed": "Observed active",
        }),
        use_container_width=True,
        hide_index=True,
    )

elif selected_view == "📊 Model Benchmarks & Explainability":
    st.subheader("📊 Model Benchmarks")
    metrics = engine.get_models_summary()
    tab_a, tab_b = st.tabs(["Task A: Flood Onset", "Task B: Active Flood State"])

    with tab_a:
        rows_a = []
        for model_name, summary in metrics.get("task_a_onset", {}).items():
            rows_a.append({
                "Model": model_name,
                "Threshold": summary.get("threshold", 0.0),
                "Precision": summary.get("precision", 0.0),
                "Recall": summary.get("recall", 0.0),
                "F1": summary.get("f1", 0.0),
                "ROC-AUC": summary.get("roc_auc", 0.0),
            })
        st.dataframe(pd.DataFrame(rows_a), use_container_width=True, hide_index=True)

    with tab_b:
        rows_b = []
        for model_name, summary in metrics.get("task_b_active", {}).items():
            rows_b.append({
                "Model": model_name,
                "Threshold": summary.get("threshold", 0.0),
                "Precision": summary.get("precision", 0.0),
                "Recall": summary.get("recall", 0.0),
                "F1": summary.get("f1", 0.0),
                "ROC-AUC": summary.get("roc_auc", 0.0),
            })
        st.dataframe(pd.DataFrame(rows_b), use_container_width=True, hide_index=True)

elif selected_view == "🛰️ Catchment Geospatial Telemetry":
    chars_path = REPO_ROOT / "data" / "processed" / "target_catchment_characteristics.csv"
    if chars_path.exists():
        chars_df = pd.read_csv(chars_path)
        chars_df["clean_id"] = chars_df["GaugeID"].map(clean_gauge_id)
        gauge_choice = st.selectbox(
            "Select catchment profile",
            chars_df["clean_id"].tolist(),
            format_func=lambda x: f"Gauge {x} — {engine.get_station_info(x).get('station_name', 'Unknown')}"
        )
        row = chars_df[chars_df["clean_id"] == gauge_choice].iloc[0]
        info = engine.get_station_info(gauge_choice)
        st.markdown(f"### {info.get('station_name')} (Gauge {gauge_choice})")
        st.write(f"**River:** {info.get('river')} | **Basin:** {info.get('basin')} | **Coordinates:** {info.get('latitude')}°N, {info.get('longitude')}°E")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Drainage Area", f"{float(row.get('Drainage Area', 0)):,.1f} km²")
        c2.metric("Catchment Relief", f"{float(row.get('Catchment Relief', 0)):,.0f} m")
        c3.metric("Stream Order", int(row.get("Stream Order", 1)))
        c4.metric("Drainage Density", f"{float(row.get('Drainage Density', 0)):.5f}")
        st.write(f"**Population count:** {float(row.get('Population Count', 0)):,.0f}")
        st.write(f"**Urban percentage:** {float(row.get('Urban percentage', 0)):.1f}%")