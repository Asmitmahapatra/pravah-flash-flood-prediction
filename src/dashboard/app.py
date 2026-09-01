from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import folium
from folium.plugins import Fullscreen
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.inference.predictor import PravahInferenceEngine, clean_gauge_id

st.set_page_config(
    page_title="PRAVAH — Flash-Flood Early Warning Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- LOGO HELPER ---
LOGO_PATH = REPO_ROOT / "src" / "dashboard" / "assets" / "pravah_logo.svg"


def get_logo_html(width: int = 240) -> str:
    if LOGO_PATH.exists():
        svg_code = LOGO_PATH.read_text(encoding="utf-8")
        b64 = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
        return f'<img src="data:image/svg+xml;base64,{b64}" width="{width}px" style="margin-bottom: 10px;" />'
    return "<h2>🌊 PRAVAH</h2>"


# --- CACHED RESOURCES ---
@st.cache_resource
def get_inference_engine() -> PravahInferenceEngine:
    return PravahInferenceEngine()


@st.cache_data
def get_catchments_geojson() -> Dict[str, Any]:
    path = REPO_ROOT / "data" / "processed" / "target_catchments.geojson"
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


engine = get_inference_engine()
geojson_data = get_catchments_geojson()

# --- COLOR MAPS ---
ALERT_COLOR_MAP = {
    "NORMAL": "#2ecc71",     # Green
    "ADVISORY": "#f1c40f",   # Yellow
    "WARNING": "#e67e22",    # Orange
    "EMERGENCY": "#e74c3c",  # Red
}

ALERT_EMOJI_MAP = {
    "NORMAL": "🟢 Normal",
    "ADVISORY": "🟡 Advisory",
    "WARNING": "🟠 Warning",
    "EMERGENCY": "🔴 Emergency",
}


# --- SIDEBAR ---
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
    st.markdown("### 🤖 Active ML Models")
    onset_model = st.selectbox("Onset Classifier", ["RandomForest", "XGBoost", "LightGBM"], index=0)
    active_model = st.selectbox("Active State Classifier", ["XGBoost", "LightGBM", "RandomForest"], index=0)
    
    st.divider()
    st.info("📍 **Domain:** 20 Open Gauge Stations across the 100 km Maharashtra Western Ghats corridor proxy.")


# --- MAIN HEADER ---
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    st.markdown(get_logo_html(width=160), unsafe_allow_html=True)
with header_col2:
    st.title("PRAVAH — Early Warning & Geospatial Intelligence System")
    st.caption("AI-Driven Multi-Source Spatio-Temporal Flash-Flood Prediction for Maharashtra Western Ghats Catchments")

st.divider()


# =========================================================================
# TAB 1: LIVE RISK & CATCHMENT MAP
# =========================================================================
if selected_view == "🗺️ Live Risk & Catchment Map":
    st.subheader("🗺️ Live Catchment Risk Map & Rainfall Scenario Simulator")
    
    col_map, col_sim = st.columns([1.5, 1.2])
    
    # Rainfall presets
    PRESETS = {
        "Custom Sliders": None,
        "Dry Season (0 mm/day)": [0.0] * 10,
        "Moderate Monsoon (20–45 mm/day)": [10.0, 15.0, 20.0, 30.0, 25.0, 40.0, 45.0, 35.0, 25.0, 35.0],
        "Heavy Storm Surge (70–130 mm/day)": [20.0, 35.0, 55.0, 80.0, 110.0, 130.0, 140.0, 115.0, 90.0, 105.0],
        "August 2019 Extreme Deluge (150–280 mm/day)": [45.0, 85.0, 130.0, 190.0, 250.0, 280.0, 260.0, 210.0, 180.0, 220.0],
    }
    
    with col_sim:
        st.markdown("#### 🌧️ Live Rainfall Simulator")
        gauge_list = engine.registered_gauges
        gauge_labels = {g: f"{g} — {engine.get_station_info(g).get('station_name', 'Unknown')}" for g in gauge_list}
        selected_gauge = st.selectbox("Target Station Catchment", gauge_list, format_func=lambda x: gauge_labels[x], index=19)
        
        preset_choice = st.selectbox("Quick Rainfall Preset Scenario", list(PRESETS.keys()), index=0)
        
        rainfall_values = []
        if preset_choice != "Custom Sliders" and PRESETS[preset_choice] is not None:
            rainfall_values = PRESETS[preset_choice]
            st.markdown(f"**Applied Scenario (Days T-10 to T-1):**")
            st.code(f"{rainfall_values}")
        else:
            st.markdown("**10-Day Pre-Cutoff Daily Rainfall ($P_{T-10} \\dots P_{T-1}$ mm):**")
            c1, c2 = st.columns(2)
            for i in range(10):
                target_col = c1 if i < 5 else c2
                val = target_col.number_input(f"Day T-{10-i} (mm)", min_value=0.0, max_value=500.0, value=25.0 if i >= 6 else 5.0, step=5.0, key=f"rain_day_{i}")
                rainfall_values.append(float(val))
        
        # Run prediction
        pred_res = engine.predict_live(
            selected_gauge,
            rainfall_values,
            onset_model_name=onset_model,
            active_model_name=active_model,
        )
        
        tier = pred_res["alert_tier"]["tier"]
        color = pred_res["alert_tier"]["color"]
        rec = pred_res["alert_tier"]["recommendation"]
        
        st.divider()
        st.markdown(f"#### Alert Status: **:{color.lower()}[{ALERT_EMOJI_MAP.get(tier, tier)}]**")
        st.info(f"**Action Protocol:** {rec}")
        
        kpi1, kpi2 = st.columns(2)
        kpi1.metric(
            label="1-Day Ahead Onset Risk",
            value=f"{pred_res['task_a_onset']['probability']:.1%}",
            delta="HIGH ONSET RISK" if pred_res['task_a_onset']['is_flood_onset_predicted'] else "NORMAL",
            delta_color="inverse" if pred_res['task_a_onset']['is_flood_onset_predicted'] else "normal",
        )
        kpi2.metric(
            label="Active Flood State",
            value=f"{pred_res['task_b_active']['probability']:.1%}",
            delta="ACTIVE INUNDATION" if pred_res['task_b_active']['is_active_flood_predicted'] else "INACTIVE",
            delta_color="inverse" if pred_res['task_b_active']['is_active_flood_predicted'] else "normal",
        )
        
        # Antecedent Bar Chart
        fig_rain = go.Figure(data=[
            go.Bar(
                x=[f"T-{10-i}" for i in range(10)],
                y=rainfall_values,
                marker_color="#0072ff"
            )
        ])
        fig_rain.update_layout(
            title="Antecedent 10-Day Rainfall Profile",
            xaxis_title="Days Prior to Forecast Cutoff",
            yaxis_title="Precipitation (mm/day)",
            height=230,
            margin=dict(l=20, r=20, t=35, b=20),
        )
        st.plotly_chart(fig_rain, use_container_width=True)

    with col_map:
        st.markdown("#### 🗺️ Geospatial Catchment Boundary Map")
        
        # 100% Free OpenStreetMap tile layer (ZERO API Key required!)
        m = folium.Map(
            location=[18.0, 74.3],
            zoom_start=8,
            tiles="OpenStreetMap",
            control_scale=True,
        )
        
        # Add Topography layer option
        folium.TileLayer(
            tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
            attr='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
            name="Topography (OpenTopoMap)",
        ).add_to(m)
        
        folium.LayerControl(position="topright").add_to(m)
        Fullscreen(position="topleft").add_to(m)
        
        # Add Catchment Polygons
        for feature in geojson_data.get("features", []):
            gid = clean_gauge_id(feature.get("properties", {}).get("GaugeID", ""))
            info = engine.get_station_info(gid)
            is_selected = (gid == selected_gauge)
            
            poly_color = ALERT_COLOR_MAP.get(tier if is_selected else "NORMAL", "#2ecc71")
            
            folium.GeoJson(
                feature,
                style_function=lambda x, is_sel=is_selected, p_color=poly_color: {
                    "fillColor": p_color if is_sel else "#3498db",
                    "color": "#1a252f",
                    "weight": 3.5 if is_sel else 1.2,
                    "fillOpacity": 0.7 if is_sel else 0.3,
                },
                tooltip=(
                    f"<b>Station:</b> {info.get('station_name')} (Gauge {gid})<br>"
                    f"<b>River:</b> {info.get('river')}<br>"
                    f"<b>Danger Level:</b> {info.get('danger_level_m')} m"
                ),
            ).add_to(m)
            
            # Station Pin Marker
            lat = info.get("latitude", 0.0)
            lon = info.get("longitude", 0.0)
            if lat > 0 and lon > 0:
                marker_color = (
                    "red" if is_selected and tier in ["WARNING", "EMERGENCY"]
                    else ("orange" if is_selected and tier == "ADVISORY" else "blue")
                )
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>{info.get('station_name')}</b><br>River: {info.get('river')}<br>Danger: {info.get('danger_level_m')} m",
                    icon=folium.Icon(color=marker_color, icon="tint", prefix="fa"),
                ).add_to(m)
        
        st_folium(m, width=750, height=620)


# =========================================================================
# TAB 2: HISTORICAL SIMULATION REPLAY
# =========================================================================
elif selected_view == "⏳ Historical Simulation Replay":
    st.subheader("⏳ Historical Flood Event Replay & Multi-Station Simulation (1964–2020)")
    
    HISTORICAL_HIGHLIGHTS = {
        "2019-08-05 (Catastrophic Kolhapur / Sangli Flood Surge)": "2019-08-05",
        "2019-08-04 (August 2019 Monsoon Peak Flood Day)": "2019-08-04",
        "2005-07-26 (Record Western Maharashtra Deluge)": "2005-07-26",
        "2006-08-06 (Krishna Basin Regional Flood Event)": "2006-08-06",
        "1989-07-24 (Historical Severe Western Ghats Monsoon)": "1989-07-24",
        "2018-08-15 (Moderate Monsoon State)": "2018-08-15",
        "2015-02-10 (Dry Winter Baseline Day)": "2015-02-10",
    }
    
    col_date, col_summary = st.columns([1.2, 1.8])
    with col_date:
        event_choice = st.selectbox("Benchmark Event Quick Selection", list(HISTORICAL_HIGHLIGHTS.keys()), index=1)
        default_date = HISTORICAL_HIGHLIGHTS[event_choice]
        selected_date = st.text_input("Or Enter Any Historical Date (1964-12-01 to 2020-05-27)", value=default_date)
    
    sim_data = engine.predict_historical_date(
        selected_date,
        onset_model_name=onset_model,
        active_model_name=active_model,
    )
    
    with col_summary:
        st.markdown(f"#### Regional Simulation Summary for **{selected_date}**")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Active Gauges", sim_data["total_stations_active"])
        k2.metric("🔴 Emergency Alerts", sim_data["emergency_count"])
        k3.metric("🟠 Warnings", sim_data["warning_count"])
        k4.metric("🟢 Normal Gauges", sim_data["normal_count"])
    
    st.divider()
    st.markdown("#### Catchment-Level Predictions vs. CWC Ground Truth Observations")
    
    sim_df = pd.DataFrame(sim_data["catchments"])
    sim_df["Alert Status"] = sim_df["alert_tier"].map(lambda x: ALERT_EMOJI_MAP.get(x, x))
    sim_df["Actual CWC Ground Event"] = sim_df["actual_active_observed"].map({0: "⚪ No Flood", 1: "🟡 Flood", 2: "🔴 Severe Flood"})
    
    display_cols = [
        "gauge_id",
        "station_name",
        "river",
        "Alert Status",
        "onset_probability",
        "active_probability",
        "Actual CWC Ground Event",
        "rain_1d_mm",
        "rain_3d_sum_mm",
        "rain_7d_sum_mm",
    ]
    
    st.dataframe(
        sim_df[display_cols].rename(columns={
            "gauge_id": "Gauge ID",
            "station_name": "Station",
            "river": "River",
            "onset_probability": "Onset Prob",
            "active_probability": "Active Prob",
            "rain_1d_mm": "Rain 1d (mm)",
            "rain_3d_sum_mm": "Rain 3d (mm)",
            "rain_7d_sum_mm": "Rain 7d (mm)",
        }),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================================
# TAB 3: MODEL BENCHMARKS & EXPLAINABILITY
# =========================================================================
elif selected_view == "📊 Model Benchmarks & Explainability":
    st.subheader("📊 Machine Learning Benchmark Comparisons & Feature Importance")
    
    metrics = engine.get_models_summary()
    
    tab_a, tab_b = st.tabs(["Task A: Flood Onset Prediction", "Task B: Daily Active Flood State"])
    
    with tab_a:
        st.markdown("#### Task A — 1-Day Ahead Flood Onset Detection (`target_onset > 0`)")
        st.caption("Evaluated Out-of-Sample on Unseen Test Years (2016–2020)")
        
        rows_a = []
        for m_name, m_dict in metrics.get("task_a_onset", {}).items():
            rows_a.append({
                "Model": m_name,
                "Tuned Threshold": round(m_dict.get("threshold", 0), 4),
                "Precision": f"{m_dict.get('precision', 0):.2%}",
                "Recall": f"{m_dict.get('recall', 0):.2%}",
                "F1 Score": round(m_dict.get("f1", 0), 4),
                "CSI (Threat Score)": round(m_dict.get("csi", 0), 4),
                "ROC-AUC": round(m_dict.get("roc_auc", 0), 4),
                "Average Precision (PR-AUC)": round(m_dict.get("average_precision", 0), 4),
            })
        st.dataframe(pd.DataFrame(rows_a), use_container_width=True, hide_index=True)
        
        # Feature Importance Chart
        rf_feats = metrics.get("task_a_onset", {}).get("RandomForest", {}).get("top_15_features", [])
        if rf_feats:
            df_feat = pd.DataFrame(rf_feats).sort_values("importance", ascending=True)
            df_feat["feature_name"] = df_feat["feature"].str.replace("num__", "")
            
            fig = px.bar(
                df_feat,
                x="importance",
                y="feature_name",
                orientation="h",
                title="Random Forest Top 15 Feature Importances (Task A: Onset)",
                labels={"importance": "Gini Importance", "feature_name": "Predictor Feature"},
                color="importance",
                color_continuous_scale="Blues",
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

    with tab_b:
        st.markdown("#### Task B — Daily Active Flood State Classification (`target_active > 0`)")
        st.caption("Evaluated Out-of-Sample on Unseen Test Years (2016–2020)")
        
        rows_b = []
        for m_name, m_dict in metrics.get("task_b_active", {}).items():
            rows_b.append({
                "Model": m_name,
                "Tuned Threshold": round(m_dict.get("threshold", 0), 4),
                "Precision": f"{m_dict.get('precision', 0):.2%}",
                "Recall": f"{m_dict.get('recall', 0):.2%}",
                "F1 Score": round(m_dict.get("f1", 0), 4),
                "CSI (Threat Score)": round(m_dict.get("csi", 0), 4),
                "ROC-AUC": round(m_dict.get("roc_auc", 0), 4),
                "Average Precision (PR-AUC)": round(m_dict.get("average_precision", 0), 4),
            })
        st.dataframe(pd.DataFrame(rows_b), use_container_width=True, hide_index=True)
        
        # XGBoost Feature Importance
        xgb_feats = metrics.get("task_b_active", {}).get("XGBoost", {}).get("top_15_features", [])
        if xgb_feats:
            df_xgb = pd.DataFrame(xgb_feats).sort_values("importance", ascending=True)
            df_xgb["feature_name"] = df_xgb["feature"].str.replace("num__", "")
            
            fig_b = px.bar(
                df_xgb,
                x="importance",
                y="feature_name",
                orientation="h",
                title="XGBoost Top 15 Feature Importances (Task B: Active State)",
                labels={"importance": "Gain Importance", "feature_name": "Predictor Feature"},
                color="importance",
                color_continuous_scale="Tealgrn",
            )
            fig_b.update_layout(height=450)
            st.plotly_chart(fig_b, use_container_width=True)


# =========================================================================
# TAB 4: CATCHMENT GEOSPATIAL TELEMETRY
# =========================================================================
elif selected_view == "🛰️ Catchment Geospatial Telemetry":
    st.subheader("🛰️ Catchment Morphometric, Terrain & Socio-Economic Profiles")
    
    chars_path = REPO_ROOT / "data" / "processed" / "target_catchment_characteristics.csv"
    if chars_path.exists():
        chars_df = pd.read_csv(chars_path)
        chars_df["clean_id"] = chars_df["GaugeID"].map(clean_gauge_id)
        
        gauge_choice = st.selectbox(
            "Select Catchment for In-Depth Profile",
            chars_df["clean_id"].tolist(),
            format_func=lambda x: f"Gauge {x} — {engine.get_station_info(x).get('station_name', 'Unknown')}"
        )
        
        row = chars_df[chars_df["clean_id"] == gauge_choice].iloc[0]
        info = engine.get_station_info(gauge_choice)
        
        st.markdown(f"### Profile: **{info.get('station_name')}** (Gauge {gauge_choice})")
        st.write(f"**River:** {info.get('river')} | **Basin:** {info.get('basin')} | **Coordinates:** {info.get('latitude')}°N, {info.get('longitude')}°E")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Drainage Area", f"{float(row.get('Drainage Area', 0)):,.1f} km²")
        c2.metric("Catchment Relief", f"{float(row.get('Catchment Relief', 0)):,.0f} m")
        c3.metric("Stream Order", int(row.get("Stream Order", 1)))
        c4.metric("Drainage Density", f"{float(row.get('Drainage Density', 0)):.5f}")
        
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Population Count", f"{float(row.get('Population Count', 0)):,.0f}")
        c6.metric("Population Density", f"{float(row.get('Population Density', 0)):.1f} /km²")
        c7.metric("Road Density", f"{float(row.get('Road Density', 0)):.1f} km/km²")
        c8.metric("Urban Percentage", f"{float(row.get('Urban percentage', 0)):.1f}%")
        
        st.divider()
        st.markdown("#### Environmental & Geological Classifications")
        e1, e2, e3 = st.columns(3)
        e1.info(f"🌿 **Land Cover:** {row.get('Land cover', 'N/A')}")
        e2.info(f"🏔️ **Soil Type:** {row.get('Soil type', 'N/A')}")
        e3.info(f"🪨 **Lithology:** {row.get('lithology type', 'N/A')}")
        
        st.markdown("#### Bioclimatic Characteristics")
        b1, b2, b3, b4 = st.columns(4)
        b1.write(f"**Annual Mean Temp:** {float(row.get('Annual Mean Temperature', 0)):.1f} °C")
        b2.write(f"**Annual Precipitation:** {float(row.get('Annual Precipitation', 0)):.0f} mm")
        b3.write(f"**Precip Seasonality:** {float(row.get('Precipitation Seasonality', 0)):.1f}")
        b4.write(f"**Climate Type:** {row.get('KoppenGeiger Climate Type', 'N/A')}")
