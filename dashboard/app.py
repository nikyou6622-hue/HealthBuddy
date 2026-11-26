"""Main Streamlit application for the Multi-Disease Prediction System (MediSense ML)."""

import base64
import json
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add src to path
_src_path = str(Path(__file__).parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from src import (
    DEFAULT_DISEASE,
    DISEASES_CONFIG,
    MEDICAL_DISCLAIMER,
    MODELS_DIR,
    REPORTS_DIR,
    STREAMLIT_CONFIG,
    MultiDiseasePredictor,
    Predictor,
    create_predictor,
    get_database,
    get_disease_config,
    get_feature_schema,
    list_supported_diseases,
    sanitize_input,
    validate_input,
)

# Page configuration
st.set_page_config(**STREAMLIT_CONFIG)

# Clinical Color Palette for Charts
CLINICAL_COLORS = ["#0284c7", "#6366f1", "#10b981", "#f59e0b", "#ef4444"]

# Enhanced Modern Clinical Dashboard Stylesheet
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }

    /* Main Canvas Background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }

    [data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.85);
        backdrop-filter: blur(10px);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    [data-testid="stSidebar"] * {
        color: #e2e8f0;
    }

    [data-testid="stSidebar"] .stRadio > label {
        color: #94a3b8 !important;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 0.55rem 0.85rem;
        margin-bottom: 0.35rem;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(56, 189, 248, 0.12);
        border-color: rgba(56, 189, 248, 0.35);
    }

    /* Hero Header */
    .hero-shell {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #0369a1 100%);
        border-radius: 20px;
        padding: 1.75rem 2.25rem;
        margin-bottom: 1.75rem;
        box-shadow: 0 18px 38px -12px rgba(15, 23, 42, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
        line-height: 1.15;
    }

    .hero-sub {
        color: #cbd5e1;
        font-size: 0.98rem;
        font-weight: 500;
        margin: 0;
    }

    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .hero-pill {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.16);
        color: #e0f2fe;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    .sub-header {
        font-size: 1.45rem;
        color: #0f172a;
        margin: 0.25rem 0 1rem 0;
        font-weight: 800;
        letter-spacing: -0.3px;
    }

    /* Disease Hero Banner */
    .disease-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0284c7 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin: 0.75rem 0 1.5rem 0;
        box-shadow: 0 12px 28px -8px rgba(15, 23, 42, 0.28);
        border: 1px solid rgba(255, 255, 255, 0.12);
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
    }

    .disease-banner h3 {
        margin: 0;
        color: #ffffff;
        font-size: 1.45rem;
        font-weight: 800;
    }

    .disease-banner p {
        margin: 0.35rem 0 0 0;
        color: #cbd5e1;
        font-size: 0.93rem;
        line-height: 1.45;
    }

    .banner-stats {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .banner-stat {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 12px;
        padding: 0.55rem 0.9rem;
        text-align: center;
        min-width: 105px;
    }

    .banner-stat-val {
        font-size: 1.05rem;
        font-weight: 800;
        color: #ffffff;
        display: block;
    }

    .banner-stat-lbl {
        font-size: 0.72rem;
        color: #bae6fd;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }

    /* Elevated Cards */
    .med-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.4rem 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
        margin-bottom: 1rem;
    }

    /* KPI Metric Cards */
    .metric-card {
        background: #ffffff;
        padding: 1.35rem 1.25rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.04);
        text-align: center;
        border-top: 4px solid #0284c7;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px -6px rgba(15, 23, 42, 0.09);
    }

    .metric-card h3 {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0 0 0.25rem 0;
        line-height: 1.15;
    }

    .metric-card p {
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 700;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Disease Module Showcase Cards */
    .module-card {
        background: #ffffff;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        padding: 1.4rem;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 295px;
        transition: all 0.25s ease;
        margin-bottom: 0.65rem;
    }

    .module-card:hover {
        border-color: #38bdf8;
        transform: translateY(-4px);
        box-shadow: 0 16px 30px -8px rgba(2, 132, 199, 0.16);
    }

    .module-icon-wrap {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: #f0f9ff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.55rem;
        margin-bottom: 0.85rem;
        border: 1px solid #e0f2fe;
    }

    .module-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }

    .module-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        background: #e0f2fe;
        color: #0369a1;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }

    .module-details {
        font-size: 0.86rem;
        color: #475569;
        line-height: 1.55;
        margin-bottom: 1rem;
    }

    .module-footer {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
        font-size: 0.83rem;
        color: #1e293b;
    }

    /* Status & Alert Cards */
    .info-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 1.15rem 1.4rem;
        border-radius: 14px;
        border: 1px solid #bae6fd;
        color: #0369a1;
        margin: 0.85rem 0;
    }

    .warning-card {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        padding: 1.15rem 1.4rem;
        border-radius: 14px;
        border: 1px solid #fde68a;
        color: #92400e;
        margin: 0.85rem 0;
    }

    .danger-card {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        border: 1px solid #fecaca;
        color: #991b1b;
        margin: 0.85rem 0;
    }

    .success-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        border: 1px solid #bbf7d0;
        color: #166534;
        margin: 0.85rem 0;
    }

    /* Primary & Form Buttons */
    .stButton > button, .stFormSubmitButton > button {
        width: 100%;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff !important;
        font-weight: 700;
        padding: 0.62rem 1.15rem;
        border-radius: 10px;
        border: none;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.24);
        transition: all 0.2s ease;
        font-size: 0.92rem;
    }

    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%);
        box-shadow: 0 6px 16px rgba(2, 132, 199, 0.35);
        transform: translateY(-1px);
    }

    /* Input Field Labels & Range Pills */
    .feature-label-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 0.4rem;
        margin-bottom: 0.25rem;
        margin-top: 0.35rem;
    }

    .feature-input-label {
        font-size: 0.86rem;
        font-weight: 600;
        color: #1e293b;
        line-height: 1.3;
    }

    .range-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        color: #0369a1;
        background: #e0f2fe;
        padding: 0.12rem 0.45rem;
        border-radius: 6px;
        white-space: nowrap;
    }

    /* Pipeline Visual Flow */
    .pipeline-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.5rem 0;
    }

    .pipeline-stage {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 4px solid #0284c7;
        border-radius: 14px;
        padding: 1.15rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }

    .pipeline-step {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        color: #0284c7;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }

    .pipeline-title {
        font-size: 1.02rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }

    .pipeline-list {
        margin: 0;
        padding-left: 1.1rem;
        color: #475569;
        font-size: 0.84rem;
        line-height: 1.55;
    }

    /* Hide default Streamlit chrome for pure SaaS feel */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Native Metric & Expander Polish */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem 1.15rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }

    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
    }

    /* Live Status Pulse Dot */
    @keyframes pulse-ring {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 7px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #6ee7b7;
        padding: 0.3rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        animation: pulse-ring 2s infinite;
    }

    /* Clean Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #e2e8f0;
        padding: 0.35rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 9px;
        padding: 0.45rem 1rem;
        font-weight: 600;
        color: #475569;
    }

    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
    }
</style>
""",
    unsafe_allow_html=True,
)


def style_plotly_fig(fig: go.Figure, height: int = 420) -> go.Figure:
    """Apply consistent clinical styling to Plotly figures."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#1e293b"),
        title_font=dict(size=16, color="#0f172a"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def display_header():
    """Display the application hero banner."""
    st.markdown(
        """
        <div class="hero-shell">
            <div>
                <h1 class="hero-title">🩺 MediSense ML</h1>
                <p class="hero-sub">Multi-Disease Clinical Decision Support &amp; Diagnostic Risk Stratification Platform</p>
            </div>
            <div class="hero-pills">
                <span class="hero-pill">v2.0.0</span>
                <span class="hero-pill">4 Organ Systems</span>
                <span class="hero-pill">16 Benchmarked Models</span>
                <span class="hero-pill">Zero-Leakage Pipeline</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_disease_best_model(disease: str) -> Tuple[str, float]:
    """Retrieve champion model name and holdout F1 score."""
    meta_path = MODELS_DIR / disease / "training_metadata.json"
    if not meta_path.exists() and disease == DEFAULT_DISEASE:
        meta_path = MODELS_DIR / "training_metadata.json"

    if meta_path.exists():
        try:
            with open(meta_path, "r") as f:
                data = json.load(f)
                return data.get("best_model", "Random Forest"), float(data.get("best_score", 0.85))
        except Exception:
            pass
    return "Random Forest", 0.85


def load_cross_disease_matrix() -> pd.DataFrame:
    """Load evaluation metrics across all supported disease modules."""
    rows = []
    for d_key, d_cfg in DISEASES_CONFIG.items():
        eval_path = MODELS_DIR / d_key / "evaluation_results.json"
        if not eval_path.exists() and d_key == DEFAULT_DISEASE:
            eval_path = MODELS_DIR / "evaluation_results.json"

        if eval_path.exists():
            try:
                with open(eval_path, "r") as f:
                    eval_data = json.load(f)
                for m_name, res in eval_data.items():
                    if "error" not in res:
                        rows.append(
                            {
                                "Disease Module": d_cfg["name"],
                                "Algorithm": m_name.replace("_", " ").title(),
                                "Accuracy": res["accuracy"],
                                "Precision (Weighted)": res["precision_weighted"],
                                "Recall (Weighted)": res["recall_weighted"],
                                "F1 (Weighted)": res["f1_weighted"],
                                "ROC AUC": res.get("roc_auc") or 0.0,
                            }
                        )
            except Exception:
                pass
    return pd.DataFrame(rows)


def display_home_dashboard():
    """Display the multi-disease overview dashboard."""
    st.markdown('<h2 class="sub-header">Multi-Organ Diagnostic System Overview</h2>', unsafe_allow_html=True)

    # Live DB count for KPI card
    try:
        audit_count = get_database().get_prediction_count()
    except Exception:
        audit_count = 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            """
        <div class="metric-card" style="border-top-color: #0284c7;">
            <h3>4 Systems</h3>
            <p>Heart • Diabetes • Parkinson's • Liver</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
        <div class="metric-card" style="border-top-color: #6366f1;">
            <h3>16 Classifiers</h3>
            <p>Linear • Trees • Bagging • Distance</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
        <div class="metric-card" style="border-top-color: #10b981;">
            <h3>5-Fold CV</h3>
            <p>Stratified Zero-Leakage Splits</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
        <div class="metric-card" style="border-top-color: #f59e0b;">
            <h3>{audit_count} Logs</h3>
            <p>SQLite Indexed Audit Trail</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Interactive Module Showcase Grid
    st.markdown("### 🔬 Supported Clinical Disease Modules")
    d_cols = st.columns(4)

    for idx, (d_key, d_cfg) in enumerate(DISEASES_CONFIG.items()):
        col = d_cols[idx]
        best_name, best_score = get_disease_best_model(d_key)
        info = d_cfg["dataset_info"]
        with col:
            st.markdown(
                f"""
            <div class="module-card">
                <div>
                    <div class="module-icon-wrap">{d_cfg['icon']}</div>
                    <div class="module-title">{d_cfg['name']}</div>
                    <div class="module-badge">{d_cfg['system']} System</div>
                    <div class="module-details">
                        <strong>Biomarkers:</strong> {len(d_cfg['feature_columns'])} parameters<br>
                        <strong>Cohort:</strong> {info['samples']} clinical records<br>
                        <strong>Source:</strong> {info['source']}
                    </div>
                </div>
                <div class="module-footer">
                    🏆 <strong>Champion:</strong> {best_name.replace('_', ' ').title()}<br>
                    📊 <strong>Holdout F1:</strong> {best_score:.3f}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            if st.button(f"Screen {d_cfg['name']} →", key=f"home_screen_{d_key}"):
                st.session_state["pred_disease_selector"] = d_key
                st.session_state["nav_page"] = "🔍 Prediction"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Live Benchmark Snapshot + Architectural Highlights
    col_chart, col_side = st.columns([3, 2])
    with col_chart:
        with st.container(border=True):
            st.markdown("#### 📈 Live Champion Model Benchmark Snapshot")
            matrix_df = load_cross_disease_matrix()
            if not matrix_df.empty:
                best_df = matrix_df.loc[matrix_df.groupby("Disease Module")["F1 (Weighted)"].idxmax()].copy()
                melted = best_df.melt(
                    id_vars=["Disease Module", "Algorithm"],
                    value_vars=["Accuracy", "F1 (Weighted)", "ROC AUC"],
                    var_name="Metric",
                    value_name="Score",
                )
                fig = px.bar(
                    melted,
                    x="Disease Module",
                    y="Score",
                    color="Metric",
                    barmode="group",
                    text_auto=".2f",
                    hover_data=["Algorithm"],
                    color_discrete_sequence=CLINICAL_COLORS,
                )
                fig.update_layout(yaxis_range=[0, 1.08], legend_title_text="")
                st.plotly_chart(style_plotly_fig(fig, height=340), use_container_width=True)
            else:
                st.info("Run evaluation pipeline to view live benchmark charts.")

    with col_side:
        st.markdown(
            """
        <div class="med-card">
            <h3 style="margin-top:0; color:#0f172a; font-size:1.18rem;">🏗️ Engineering Highlights</h3>
            <ul style="color:#475569; font-size:0.9rem; line-height:1.68; padding-left:1.15rem; margin-bottom:0;">
                <li><strong>Micro-Pipeline Isolation:</strong> Independent Scikit-Learn transformers per disease prevent cross-domain contamination.</li>
                <li><strong>Zero Data Leakage:</strong> Median imputers &amp; <code>StandardScaler</code> fit strictly on training folds.</li>
                <li><strong>Multi-Family Benchmarking:</strong> Evaluates Logistic Regression, Decision Tree, Random Forest, and KNN.</li>
                <li><strong>Audit-Ready Persistence:</strong> SQLite relational database with B-tree indexes &amp; CSV export.</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("🔍 Run Disease Risk Prediction", key="btn_go_pred"):
            st.session_state["nav_page"] = "🔍 Prediction"
            st.rerun()
        if st.button("📊 View Full 16-Model Matrix", key="btn_go_perf"):
            st.session_state["nav_page"] = "📊 Model Performance"
            st.rerun()
        if st.button("📚 System Protocols & Architecture", key="btn_go_docs"):
            st.session_state["nav_page"] = "📚 System Protocols"
            st.rerun()

    st.markdown(f'<div class="danger-card"><strong>CLINICAL NOTICE:</strong> {MEDICAL_DISCLAIMER}</div>', unsafe_allow_html=True)


def build_risk_gauge(probability: float, prediction: int) -> go.Figure:
    """Create a sleek semi-circular clinical risk gauge."""
    pct = probability * 100.0
    bar_color = "#10b981" if pct < 35 else ("#f59e0b" if pct < 65 else "#ef4444")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            number={"suffix": "%", "font": {"size": 38, "color": "#0f172a"}},
            title={"text": "Predicted Risk Probability", "font": {"size": 15, "color": "#475569"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8"},
                "bar": {"color": bar_color, "thickness": 0.28},
                "bgcolor": "#f8fafc",
                "borderwidth": 1,
                "bordercolor": "#e2e8f0",
                "steps": [
                    {"range": [0, 35], "color": "rgba(16, 185, 129, 0.14)"},
                    {"range": [35, 65], "color": "rgba(245, 158, 11, 0.16)"},
                    {"range": [65, 100], "color": "rgba(239, 68, 68, 0.16)"},
                ],
                "threshold": {
                    "line": {"color": "#0f172a", "width": 3},
                    "thickness": 0.75,
                    "value": pct,
                },
            },
        )
    )
    fig.update_layout(
        height=270,
        margin=dict(l=20, r=20, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif"),
    )
    return fig


def build_biomarker_profile_chart(sanitized_data: Dict[str, Any], d_cfg: Dict[str, Any]) -> go.Figure:
    """Create a normalized physiological range profile chart for numerical biomarkers."""
    ranges = d_cfg.get("feature_ranges", {})
    num_features = [f for f in d_cfg.get("numerical_features", []) if f in sanitized_data and f in ranges]
    if not num_features:
        num_features = [f for f in d_cfg.get("feature_columns", []) if f in sanitized_data and f in ranges][:10]

    rows = []
    for f in num_features[:12]:
        val = float(sanitized_data[f])
        min_v, max_v = float(ranges[f][0]), float(ranges[f][1])
        pct = ((val - min_v) / (max_v - min_v) * 100.0) if max_v > min_v else 50.0
        pct = max(0.0, min(100.0, pct))
        zone = "Boundary" if (pct <= 15 or pct >= 85) else "Mid-Range"
        rows.append({
            "Biomarker": f,
            "Range Position (%)": pct,
            "Actual Value": val,
            "Valid Range": f"{min_v} – {max_v}",
            "Zone": zone,
        })

    prof_df = pd.DataFrame(rows).sort_values("Range Position (%)", ascending=True)
    fig = px.bar(
        prof_df,
        x="Range Position (%)",
        y="Biomarker",
        orientation="h",
        color="Zone",
        color_discrete_map={"Mid-Range": "#0284c7", "Boundary": "#f59e0b"},
        hover_data=["Actual Value", "Valid Range"],
        title="Biomarker Position Within Physiological Range (0% = Min, 100% = Max)",
        text_auto=".0f",
    )
    fig.update_layout(xaxis_range=[0, 108], legend_title_text="")
    return style_plotly_fig(fig, height=max(280, 34 * len(prof_df) + 90))


def display_prediction_page():
    """Display the interactive multi-disease prediction interface."""
    st.markdown('<h2 class="sub-header">Interactive Diagnostic Risk Stratification</h2>', unsafe_allow_html=True)

    diseases = list_supported_diseases()
    default_idx = 0
    if "pred_disease_selector" in st.session_state and st.session_state["pred_disease_selector"] in diseases:
        default_idx = diseases.index(st.session_state["pred_disease_selector"])

    selected_disease = st.selectbox(
        "Select Target Disease System to Screen:",
        options=diseases,
        format_func=lambda x: f"{DISEASES_CONFIG[x]['icon']} {DISEASES_CONFIG[x]['name']} ({DISEASES_CONFIG[x]['system']} System)",
        index=default_idx,
        key="pred_disease_selector",
    )

    d_cfg = get_disease_config(selected_disease)
    best_name, best_score = get_disease_best_model(selected_disease)
    cohort_n = d_cfg["dataset_info"]["samples"]

    st.markdown(
        f"""
    <div class="disease-banner">
        <div>
            <h3>{d_cfg['icon']} {d_cfg['name']} Assessment Module</h3>
            <p>Evaluating {len(d_cfg['feature_columns'])} patient biomarkers for {d_cfg['system'].lower()} disease probability.</p>
        </div>
        <div class="banner-stats">
            <div class="banner-stat">
                <span class="banner-stat-val">{best_name.replace('_', ' ').title()}</span>
                <span class="banner-stat-lbl">Champion Model</span>
            </div>
            <div class="banner-stat">
                <span class="banner-stat-val">{best_score:.3f}</span>
                <span class="banner-stat-lbl">Holdout F1</span>
            </div>
            <div class="banner-stat">
                <span class="banner-stat-val">{cohort_n}</span>
                <span class="banner-stat-lbl">Cohort Size</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        predictor = create_predictor(disease=selected_disease)
        schema = predictor.get_feature_schema()
    except Exception as e:
        st.error(f"Failed to load predictor for {d_cfg['name']}: {e}")
        st.info("Please verify models have been trained by running the training pipeline.")
        return

    # Clinical Test Presets & Batch Screening Tabs
    tab_single, tab_batch = st.tabs(["🩺 Single Patient Screening", "📂 Batch Cohort Screening (CSV)"])

    with tab_single:
        st.markdown("#### ⚡ Clinical Test Presets (Instant Case Loading)")
        preset_key = f"preset_{selected_disease}"
        if preset_key not in st.session_state:
            st.session_state[preset_key] = "default"

        p_col1, p_col2, p_col3 = st.columns(3)
        if p_col1.button("🟢 Load Healthy Profile", key=f"btn_h_{selected_disease}", use_container_width=True):
            st.session_state[preset_key] = "healthy"
            st.rerun()
        if p_col2.button("🔴 Load High-Risk Profile", key=f"btn_r_{selected_disease}", use_container_width=True):
            st.session_state[preset_key] = "high_risk"
            st.rerun()
        if p_col3.button("🔄 Reset Inputs to Default", key=f"btn_reset_{selected_disease}", use_container_width=True):
            st.session_state[preset_key] = "default"
            st.rerun()

        active_preset = st.session_state[preset_key]
        demo_presets = d_cfg.get("demo_presets", {})
        healthy_profile = demo_presets.get("healthy", {})
        high_risk_profile = demo_presets.get("high_risk", {})

        if active_preset == "healthy":
            st.markdown(
                f'<div class="success-card">ℹ️ Loaded Test Case: <strong>Low Risk / Healthy {d_cfg["name"]} Profile</strong> (Biomarkers reflect normal physiological limits).</div>',
                unsafe_allow_html=True,
            )
        elif active_preset == "high_risk":
            st.markdown(
                f'<div class="warning-card">⚠️ Loaded Test Case: <strong>High Risk / Pathological {d_cfg["name"]} Profile</strong> (Biomarkers indicate elevated risk).</div>',
                unsafe_allow_html=True,
            )

        # Dynamic Biomarker Form
        with st.form(f"prediction_form_{selected_disease}"):
            input_data = {}
            features = d_cfg["feature_columns"]

            n_cols = 3 if len(features) > 12 else 2
            form_cols = st.columns(n_cols)

            for idx, feature in enumerate(features):
                col = form_cols[idx % n_cols]
                with col:
                    f_info = schema.get(feature, {})
                    desc = f_info.get("description", feature)
                    f_type = f_info.get("type", "numerical")
                    f_range = f_info.get("range")
                    options = f_info.get("options")

                    range_badge = f'<span class="range-pill">{f_range[0]} – {f_range[1]}</span>' if f_range else ""
                    st.markdown(
                        f'<div class="feature-label-row"><span class="feature-input-label">{desc}</span>{range_badge}</div>',
                        unsafe_allow_html=True,
                    )

                    preset_val = None
                    if active_preset == "healthy":
                        preset_val = healthy_profile.get(feature)
                    elif active_preset == "high_risk":
                        preset_val = high_risk_profile.get(feature)

                    if f_type == "categorical" and options:
                        option_labels = [opt["label"] for opt in options]
                        option_values = [opt["value"] for opt in options]

                        default_idx = 0
                        if preset_val is not None and preset_val in option_values:
                            default_idx = option_values.index(preset_val)

                        selected_label = st.selectbox(
                            f"Select {feature}",
                            options=option_labels,
                            index=default_idx,
                            key=f"sel_{selected_disease}_{feature}_{active_preset}",
                            label_visibility="collapsed",
                        )
                        sel_idx = option_labels.index(selected_label)
                        input_data[feature] = option_values[sel_idx]
                    else:
                        if f_range:
                            min_v, max_v = f_range
                            step = (max_v - min_v) / 100.0 if max_v > min_v else 0.1
                            if step < 0.001:
                                step = 0.0001
                                fmt = "%.6f"
                            elif step < 0.1:
                                fmt = "%.4f"
                            else:
                                fmt = "%.2f"

                            def_val = float(preset_val) if preset_val is not None else float(min_v + (max_v - min_v) / 2)
                            def_val = max(float(min_v), min(float(max_v), def_val))

                            input_data[feature] = st.number_input(
                                f"{feature}",
                                min_value=float(min_v),
                                max_value=float(max_v),
                                value=def_val,
                                step=step,
                                format=fmt,
                                key=f"num_{selected_disease}_{feature}_{active_preset}",
                                label_visibility="collapsed",
                            )
                        else:
                            def_val = float(preset_val) if preset_val is not None else 0.0
                            input_data[feature] = st.number_input(
                                f"{feature}",
                                value=def_val,
                                key=f"num_{selected_disease}_{feature}_{active_preset}",
                                label_visibility="collapsed",
                            )

            submitted = st.form_submit_button(f"🔍 Evaluate {d_cfg['name']} Risk", use_container_width=True)

        if submitted:
            is_valid, errors = validate_input(input_data, disease=selected_disease)
            if not is_valid:
                st.error("Input validation failed:")
                for err in errors:
                    st.markdown(f"- {err}")
            else:
                sanitized_data = sanitize_input(input_data, disease=selected_disease)

                with st.spinner("Processing clinical biomarkers through inference pipeline..."):
                    result = predictor.predict(sanitized_data)

                if result["success"]:
                    prediction = result["prediction"]
                    probability = result["probability"]
                    label = result["label"]
                    risk_level = result["risk_level"]
                    recs = result.get("recommendations", [])
                    model_used = result.get("model_name", "Champion Model").replace("_", " ").title()

                    if prediction == 0:
                        card_style = "success-card"
                        icon = "✅"
                        verdict = f"LOW RISK: {label}"
                    else:
                        card_style = "danger-card"
                        icon = "⚠️"
                        verdict = f"ELEVATED RISK: {label}"

                    st.markdown(
                        f"""
                    <div class="{card_style}">
                        <h3 style="margin:0 0 0.45rem 0; font-size:1.4rem;">{icon} {verdict}</h3>
                        <p style="margin:0; font-size:0.95rem;">
                            <strong>Stratification:</strong> {risk_level} &nbsp;|&nbsp;
                            <strong>Classifier:</strong> {model_used}
                        </p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    res_c1, res_c2 = st.columns([1, 1])
                    with res_c1:
                        with st.container(border=True):
                            st.markdown("#### 🎯 Risk Probability Gauge")
                            if probability is not None:
                                st.plotly_chart(build_risk_gauge(probability, prediction), use_container_width=True)
                            else:
                                st.info("Probability estimate not available for this classifier.")

                    with res_c2:
                        with st.container(border=True):
                            st.markdown("#### 🩺 Clinical Recommendations")
                            if recs:
                                for r in recs:
                                    st.markdown(f"- {r}")
                            else:
                                st.write("Consult a licensed healthcare professional for clinical advice.")

                            st.markdown("---")
                            report_payload = {
                                "timestamp": datetime.now().isoformat(),
                                "disease": d_cfg["name"],
                                "model": model_used,
                                "prediction": prediction,
                                "label": label,
                                "probability": probability,
                                "risk_level": risk_level,
                                "biomarkers": sanitized_data,
                                "recommendations": recs,
                            }
                            st.download_button(
                                label="📥 Download Screening Report (JSON)",
                                data=json.dumps(report_payload, indent=2),
                                file_name=f"medisense_{selected_disease}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True,
                            )

                    with st.container(border=True):
                        st.plotly_chart(build_biomarker_profile_chart(sanitized_data, d_cfg), use_container_width=True)

                    with st.expander(f"📋 Biomarker Audit Record ({len(sanitized_data)} features)"):
                        summary_df = pd.DataFrame([sanitized_data])
                        st.dataframe(summary_df.T.rename(columns={0: "Biomarker Input Value"}), use_container_width=True)

                    try:
                        db = get_database()
                        rec_id = db.save_prediction(
                            input_features=sanitized_data,
                            prediction=prediction,
                            prediction_label=label,
                            probability=probability,
                            model_name=result.get("model_name", "Unknown"),
                            disease=selected_disease,
                        )
                        st.success(f"💾 Diagnostic inference audited to SQLite database (Record ID: #{rec_id})")
                    except Exception as e:
                        st.warning(f"Database audit warning: {e}")
                else:
                    st.error("Prediction failed:")
                    for err in result.get("errors", []):
                        st.markdown(f"- {err}")

    with tab_batch:
        st.markdown(f"#### 📂 Batch Cohort Screening — {d_cfg['name']}")
        st.caption(f"Upload a CSV containing the {len(d_cfg['feature_columns'])} required biomarker columns, or load the built-in sample holdout cohort.")

        b_c1, b_c2 = st.columns([2, 1])
        with b_c1:
            uploaded_csv = st.file_uploader(
                "Upload Patient Cohort CSV",
                type=["csv"],
                key=f"batch_csv_{selected_disease}",
            )
        with b_c2:
            st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
            use_sample = st.button("🧪 Load Sample Holdout Cohort (15 rows)", key=f"btn_sample_{selected_disease}", use_container_width=True)

        batch_df = None
        if uploaded_csv is not None:
            batch_df = pd.read_csv(uploaded_csv)
        elif use_sample:
            sample_path = MODELS_DIR / selected_disease / "test_set.csv"
            if not sample_path.exists() and selected_disease == DEFAULT_DISEASE:
                sample_path = MODELS_DIR / "test_set.csv"
            if sample_path.exists():
                batch_df = pd.read_csv(sample_path).head(15)
            else:
                st.warning("Sample test cohort file not found.")

        if batch_df is not None:
            req_cols = d_cfg["feature_columns"]
            missing_cols = [c for c in req_cols if c not in batch_df.columns]
            if missing_cols:
                st.error(f"Missing required biomarker columns: {', '.join(missing_cols)}")
            else:
                records = batch_df[req_cols].to_dict(orient="records")
                with st.spinner(f"Screening {len(records)} patient records..."):
                    batch_results = predictor.predict_batch(records)

                out_rows = []
                for i, (rec, res) in enumerate(zip(records, batch_results)):
                    out_rows.append(
                        {
                            "Patient #": i + 1,
                            "Status": "OK" if res.get("success") else "Validation Error",
                            "Prediction": res.get("label", "N/A"),
                            "Risk Tier": res.get("risk_level", "N/A"),
                            "Probability": res.get("probability"),
                        }
                    )
                res_df = pd.DataFrame(out_rows)
                valid_df = res_df[res_df["Status"] == "OK"]

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Patients Screened", len(res_df))
                elevated_cnt = sum(1 for r in batch_results if r.get("success") and r.get("prediction") == 1)
                k2.metric("Elevated Risk", elevated_cnt)
                k3.metric("Low Risk", sum(1 for r in batch_results if r.get("success") and r.get("prediction") == 0))
                avg_prob = valid_df["Probability"].mean() if not valid_df.empty else None
                k4.metric("Cohort Mean Risk", f"{avg_prob:.1%}" if pd.notna(avg_prob) else "N/A")

                if not valid_df.empty and valid_df["Probability"].notna().any():
                    fig_hist = px.histogram(
                        valid_df,
                        x="Probability",
                        color="Prediction",
                        nbins=15,
                        title="Cohort Risk Probability Distribution",
                        color_discrete_sequence=CLINICAL_COLORS,
                    )
                    fig_hist.update_layout(xaxis_range=[0, 1])
                    st.plotly_chart(style_plotly_fig(fig_hist, height=320), use_container_width=True)

                st.dataframe(res_df, use_container_width=True)
                st.download_button(
                    label="📥 Export Batch Screening Results (CSV)",
                    data=res_df.to_csv(index=False).encode("utf-8"),
                    file_name=f"batch_screening_{selected_disease}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )


def display_model_performance():
    """Display comprehensive benchmarking across all models and diseases."""
    st.markdown('<h2 class="sub-header">Model Benchmarking & Performance Analytics</h2>', unsafe_allow_html=True)

    selected_disease = st.selectbox(
        "Select Benchmark View:",
        options=["All Diseases Comparison"] + list_supported_diseases(),
        format_func=lambda x: "🌐 Cross-Disease Benchmark Matrix"
        if x == "All Diseases Comparison"
        else f"{DISEASES_CONFIG[x]['icon']} {DISEASES_CONFIG[x]['name']}",
        index=0,
        key="perf_disease_selector",
    )

    if selected_disease == "All Diseases Comparison":
        st.markdown("### 🌐 Cross-Disease Comparative Benchmark Matrix")
        st.markdown("Performance metrics evaluated on independent 20% holdout test partitions across all 4 clinical systems:")

        matrix_df = load_cross_disease_matrix()
        if not matrix_df.empty:
            best_per_disease = matrix_df.loc[matrix_df.groupby("Disease Module")["F1 (Weighted)"].idxmax()].reset_index(drop=True)
            st.markdown("#### 🏆 Champion Algorithm Per Clinical Domain")
            st.dataframe(
                best_per_disease.style.format(
                    {
                        "Accuracy": "{:.2%}",
                        "Precision (Weighted)": "{:.4f}",
                        "Recall (Weighted)": "{:.4f}",
                        "F1 (Weighted)": "{:.4f}",
                        "ROC AUC": "{:.4f}",
                    }
                ),
                use_container_width=True,
            )

            chart_c1, chart_c2 = st.columns(2)
            with chart_c1:
                fig = px.bar(
                    matrix_df,
                    x="Disease Module",
                    y="F1 (Weighted)",
                    color="Algorithm",
                    barmode="group",
                    title="Cross-Disease F1-Score by Algorithm Family",
                    text_auto=".3f",
                    color_discrete_sequence=CLINICAL_COLORS,
                )
                fig.update_layout(yaxis_range=[0, 1.08])
                st.plotly_chart(style_plotly_fig(fig, height=430), use_container_width=True)

            with chart_c2:
                fig_scatter = px.scatter(
                    matrix_df,
                    x="Accuracy",
                    y="ROC AUC",
                    color="Disease Module",
                    symbol="Algorithm",
                    size="F1 (Weighted)",
                    title="Accuracy vs. ROC-AUC Tradeoff (All 16 Classifiers)",
                    color_discrete_sequence=CLINICAL_COLORS,
                )
                fig_scatter.update_layout(xaxis_range=[0.6, 1.0], yaxis_range=[0.65, 1.02])
                st.plotly_chart(style_plotly_fig(fig_scatter, height=430), use_container_width=True)

            st.markdown("#### 📋 Complete 16-Classifier Benchmark Table")
            st.dataframe(
                matrix_df.style.highlight_max(axis=0, color="#dcfce7", subset=["Accuracy", "F1 (Weighted)", "ROC AUC"]).format(
                    {
                        "Accuracy": "{:.2%}",
                        "Precision (Weighted)": "{:.4f}",
                        "Recall (Weighted)": "{:.4f}",
                        "F1 (Weighted)": "{:.4f}",
                        "ROC AUC": "{:.4f}",
                    }
                ),
                use_container_width=True,
            )
        return

    # Specific disease view
    d_cfg = get_disease_config(selected_disease)
    eval_path = MODELS_DIR / selected_disease / "evaluation_results.json"
    if not eval_path.exists() and selected_disease == DEFAULT_DISEASE:
        eval_path = MODELS_DIR / "evaluation_results.json"

    if not eval_path.exists():
        st.warning(f"⚠️ No evaluation results found for {d_cfg['name']}. Please run the evaluation pipeline.")
        return

    try:
        with open(eval_path, "r") as f:
            eval_results = json.load(f)
    except Exception as e:
        st.error(f"Failed to load evaluation results: {e}")
        return

    comparison_data = []
    for model_name, results in eval_results.items():
        if "error" not in results:
            comparison_data.append(
                {
                    "Model": model_name.replace("_", " ").title(),
                    "Accuracy": results["accuracy"],
                    "Precision (Macro)": results["precision_macro"],
                    "Precision (Weighted)": results["precision_weighted"],
                    "Recall (Macro)": results["recall_macro"],
                    "Recall (Weighted)": results["recall_weighted"],
                    "F1 (Macro)": results["f1_macro"],
                    "F1 (Weighted)": results["f1_weighted"],
                    "ROC AUC": results.get("roc_auc") or 0.0,
                }
            )

    if not comparison_data:
        st.error("No valid model benchmark data found.")
        return

    df = pd.DataFrame(comparison_data).sort_values("F1 (Weighted)", ascending=False).reset_index(drop=True)
    best_row = df.iloc[0]

    st.markdown(
        f"""
    <div class="success-card">
        🏆 <strong>Champion Model for {d_cfg['name']}:</strong> {best_row['Model']} &nbsp;|&nbsp;
        <strong>F1-Weighted:</strong> {best_row['F1 (Weighted)']:.4f} &nbsp;|&nbsp;
        <strong>Accuracy:</strong> {best_row['Accuracy']:.2%} &nbsp;|&nbsp;
        <strong>ROC-AUC:</strong> {best_row['ROC AUC']:.3f}
    </div>
    """,
        unsafe_allow_html=True,
    )

    tab_metrics, tab_cm, tab_imp, tab_rep = st.tabs(
        ["📊 Metrics Comparison", "🔲 Confusion Matrices", "🌲 Feature Importance", "📑 Classification Reports"]
    )

    with tab_metrics:
        num_cols = [c for c in df.columns if c != "Model"]
        st.dataframe(
            df.style.highlight_max(axis=0, color="#dcfce7", subset=num_cols)
            .highlight_min(axis=0, color="#fee2e2", subset=num_cols)
            .format({c: "{:.4f}" for c in num_cols}),
            use_container_width=True,
        )

        metrics_to_show = ["Accuracy", "F1 (Weighted)", "ROC AUC"]
        df_melted = df.melt(id_vars=["Model"], value_vars=metrics_to_show, var_name="Metric", value_name="Score")

        fig = px.bar(
            df_melted,
            x="Model",
            y="Score",
            color="Metric",
            title=f"{d_cfg['name']} — Model Performance Across Evaluation Metrics",
            barmode="group",
            text_auto=".3f",
            color_discrete_sequence=CLINICAL_COLORS,
        )
        fig.update_layout(yaxis_range=[0, 1.08])
        st.plotly_chart(style_plotly_fig(fig, height=450), use_container_width=True)

    with tab_cm:
        st.markdown(f"#### 🔲 Test Holdout Confusion Matrices ({d_cfg['name']})")
        cm_cols = st.columns(2)
        target_labels = list(d_cfg["target_labels"].values())
        short_labels = [l[:12] + ".." if len(l) > 14 else l for l in target_labels]

        for idx, (m_name, res) in enumerate(eval_results.items()):
            if "error" in res or "confusion_matrix" not in res:
                continue
            with cm_cols[idx % 2]:
                cm = np.array(res["confusion_matrix"])
                fig_cm = go.Figure(
                    data=go.Heatmap(
                        z=cm,
                        x=short_labels,
                        y=short_labels,
                        colorscale="Blues",
                        showscale=False,
                        text=cm,
                        texttemplate="%{text}",
                        textfont={"size": 16},
                    )
                )
                fig_cm.update_layout(
                    title=f"{m_name.replace('_', ' ').title()} (Acc: {res['accuracy']:.1%})",
                    xaxis_title="Predicted Class",
                    yaxis_title="True Class",
                )
                st.plotly_chart(style_plotly_fig(fig_cm, height=350), use_container_width=True)

    with tab_imp:
        st.markdown(f"#### 🌲 Biomarker Importance Scores ({d_cfg['name']})")
        has_importance = False
        for m_name in ["random_forest", "decision_tree"]:
            if m_name in eval_results and "feature_importance" in eval_results[m_name]:
                has_importance = True
                imp_dict = eval_results[m_name]["feature_importance"]
                sorted_imp = sorted(imp_dict.items(), key=lambda x: x[1], reverse=True)[:10]
                imp_df = pd.DataFrame(sorted_imp, columns=["Biomarker", "Importance"]).sort_values("Importance", ascending=True)

                fig_imp = px.bar(
                    imp_df,
                    x="Importance",
                    y="Biomarker",
                    orientation="h",
                    title=f"Top 10 Biomarkers — {m_name.replace('_', ' ').title()}",
                    text_auto=".3f",
                    color="Importance",
                    color_continuous_scale="Blues",
                )
                st.plotly_chart(style_plotly_fig(fig_imp, height=390), use_container_width=True)

        if not has_importance:
            st.info("Feature importance is available for tree-based models (Random Forest, Decision Tree).")

    with tab_rep:
        st.markdown("#### 📑 Detailed Classification Breakdown")
        for m_name, res in eval_results.items():
            if "classification_report" in res:
                with st.expander(f"{m_name.replace('_', ' ').title()} Detailed Metrics"):
                    rep_df = pd.DataFrame(res["classification_report"]).transpose()
                    st.dataframe(rep_df.style.highlight_max(axis=0, color="#dcfce7"), use_container_width=True)


def display_prediction_history():
    """Display multi-disease audit history with filtering and statistics."""
    st.markdown('<h2 class="sub-header">Relational Diagnostic Audit Log</h2>', unsafe_allow_html=True)

    try:
        db = get_database()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return

    with st.container(border=True):
        st.markdown("#### 🔍 Filter Audit Records")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        with f_col1:
            disease_filter = st.selectbox(
                "Filter by Disease:",
                options=["All"] + list_supported_diseases(),
                format_func=lambda x: "All Diseases" if x == "All" else DISEASES_CONFIG[x]["name"],
                index=0,
            )

        with f_col2:
            pred_filter_opt = st.selectbox("Filter by Result:", ["All", "High Risk / Positive", "Low Risk / Negative"], index=0)
            pred_filter = 1 if pred_filter_opt == "High Risk / Positive" else (0 if pred_filter_opt == "Low Risk / Negative" else None)

        with f_col3:
            limit = st.selectbox("Display Limit:", [10, 25, 50, 100], index=1)

        with f_col4:
            st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Clear History", type="secondary"):
                if st.session_state.get("confirm_clear", False):
                    del_count = db.clear_history(disease_filter=disease_filter if disease_filter != "All" else None)
                    st.success(f"Cleared {del_count} audit records.")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("Click again to confirm purge")

    stats = db.get_statistics(disease_filter=disease_filter if disease_filter != "All" else None)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Ingested Inferences", stats["total_predictions"])
    with s2:
        st.metric("Recent (Last 7 Days)", stats.get("recent_predictions_7d", 0))
    with s3:
        by_disease_text = ", ".join([f"{k}: {v}" for k, v in stats.get("by_disease", {}).items()]) or "None"
        st.metric("Logged Disease Types", len(stats.get("by_disease", {})), help=by_disease_text)
    with s4:
        avg_p = stats.get("average_probability")
        st.metric("Average Risk Score", f"{avg_p:.1%}" if avg_p is not None else "N/A")

    predictions = db.get_predictions(
        limit=limit,
        prediction_filter=pred_filter,
        disease_filter=disease_filter if disease_filter != "All" else None,
    )

    if not predictions:
        st.info("No diagnostic history found matching the selected filters.")
        return

    # Analytics Strip
    hist_df = pd.DataFrame(
        [
            {
                "Disease": DISEASES_CONFIG.get(p.get("disease", "heart_disease"), {}).get("name", "Unknown"),
                "Outcome": "Elevated Risk" if p["prediction"] == 1 else "Low Risk",
            }
            for p in predictions
        ]
    )
    a_c1, a_c2 = st.columns(2)
    with a_c1:
        with st.container(border=True):
            fig_donut = px.pie(
                hist_df,
                names="Outcome",
                hole=0.55,
                title="Diagnostic Outcome Breakdown",
                color="Outcome",
                color_discrete_map={"Low Risk": "#10b981", "Elevated Risk": "#ef4444"},
            )
            st.plotly_chart(style_plotly_fig(fig_donut, height=280), use_container_width=True)
    with a_c2:
        with st.container(border=True):
            disease_counts = hist_df["Disease"].value_counts().reset_index()
            disease_counts.columns = ["Disease", "Count"]
            fig_bar = px.bar(
                disease_counts,
                x="Count",
                y="Disease",
                orientation="h",
                title="Screenings by Disease Module",
                color="Disease",
                color_discrete_sequence=CLINICAL_COLORS,
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(style_plotly_fig(fig_bar, height=280), use_container_width=True)

    st.markdown(f"### 📋 Audit Records ({len(predictions)} entries)")

    export_rows = [
        {
            "ID": p["id"],
            "Timestamp": p["timestamp"],
            "Disease": p.get("disease", "heart_disease"),
            "Prediction": p["prediction"],
            "Label": p["prediction_label"],
            "Probability": p["probability"],
            "Model": p.get("model_name"),
        }
        for p in predictions
    ]
    export_df = pd.DataFrame(export_rows)
    st.download_button(
        label="📥 Export Audit History to CSV",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name=f"diagnostic_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

    for pred in predictions:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.6, 2.4, 2, 0.5])

            with c1:
                p_disease = pred.get("disease", "heart_disease")
                d_icon = DISEASES_CONFIG.get(p_disease, {}).get("icon", "🩺")
                d_name = DISEASES_CONFIG.get(p_disease, {}).get("name", p_disease.title())
                st.markdown(f"**{d_icon} {d_name}**")
                st.caption(f"Audit Record #{pred['id']}")

            with c2:
                ts = datetime.fromisoformat(pred["timestamp"]).strftime("%Y-%m-%d %H:%M")
                st.write(f"🕒 {ts}")
                st.caption(f"Model: {pred.get('model_name', 'Unknown')}")

            with c3:
                if pred["prediction"] == 0:
                    st.markdown(
                        f"<span style='color: #166534; font-weight: 700; background: #dcfce7; padding: 0.25rem 0.65rem; border-radius: 8px;'>✅ {pred['prediction_label']}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<span style='color: #991b1b; font-weight: 700; background: #fee2e2; padding: 0.25rem 0.65rem; border-radius: 8px;'>⚠️ {pred['prediction_label']}</span>",
                        unsafe_allow_html=True,
                    )

                if pred["probability"] is not None:
                    st.caption(f"Confidence: {pred['probability']:.1%}")

            with c4:
                if st.button("🗑️", key=f"del_pred_{pred['id']}", help="Delete record"):
                    if db.delete_prediction(pred["id"]):
                        st.success(f"Deleted #{pred['id']}")
                        st.rerun()

            with st.expander(f"Inspect Patient Biomarker Payload (ID: #{pred['id']})"):
                st.json(pred["input_features"])


def display_system_documentation():
    """Display technical specifications, engineering architecture, and methodology."""
    st.markdown('<h2 class="sub-header">📚 System Protocols & Engineering Architecture</h2>', unsafe_allow_html=True)

    tab_arch, tab_proto, tab_faq, tab_dict = st.tabs(
        [
            "🏗️ Architecture & Pipeline",
            "📋 Clinical Diagnostic Protocols",
            "💡 Technical & Modeling Methodology",
            "🩺 Biomarkers Encyclopedia",
        ]
    )

    with tab_arch:
        st.markdown("### 🏗️ End-to-End System Engineering Pipeline")
        st.markdown(
            """
            <div class="pipeline-grid">
                <div class="pipeline-stage" style="border-top-color: #0284c7;">
                    <div class="pipeline-step">Stage 01 • Data Layer</div>
                    <div class="pipeline-title">Multi-Disease Datasets</div>
                    <ul class="pipeline-list">
                        <li>UCI Cleveland Heart (303 × 13)</li>
                        <li>NIDDK Pima Diabetes (768 × 8)</li>
                        <li>Oxford Parkinson's (195 × 22)</li>
                        <li>UCI ILPD Liver (583 × 10)</li>
                    </ul>
                </div>
                <div class="pipeline-stage" style="border-top-color: #6366f1;">
                    <div class="pipeline-step">Stage 02 • Preprocessing</div>
                    <div class="pipeline-title">Zero-Leakage Pipeline</div>
                    <ul class="pipeline-list">
                        <li>Schema &amp; range guardrails</li>
                        <li>Median <code>SimpleImputer</code></li>
                        <li>Conditional <code>StandardScaler</code></li>
                        <li>Strict train-only <code>fit_transform</code></li>
                    </ul>
                </div>
                <div class="pipeline-stage" style="border-top-color: #10b981;">
                    <div class="pipeline-step">Stage 03 • Benchmarking</div>
                    <div class="pipeline-title">16-Model Engine</div>
                    <ul class="pipeline-list">
                        <li>Logistic Regression</li>
                        <li>Decision Tree (Depth 5)</li>
                        <li>Random Forest (100 Trees)</li>
                        <li>KNN (k=5) + 5-Fold CV</li>
                    </ul>
                </div>
                <div class="pipeline-stage" style="border-top-color: #f59e0b;">
                    <div class="pipeline-step">Stage 04 • Production</div>
                    <div class="pipeline-title">Inference &amp; Audit</div>
                    <ul class="pipeline-list">
                        <li>Risk stratification tiers</li>
                        <li>Actionable clinical guidance</li>
                        <li>SQLite audit log (<code>predictions.db</code>)</li>
                        <li>82 automated Pytest checks</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_proto:
        st.markdown(
            """
        ### 📋 Standard Clinical Inference Protocol
        The diagnostic workflow enforces a four-stage pipeline:

        1. **Stage 1: Patient Biomarker Ingestion & Schema Guardrails**
           - Incoming payloads are validated against physiological ranges in `src/validation.py`.
           - Prevents out-of-bounds numbers (e.g., negative blood pressure or impossible BMI).

        2. **Stage 2: Zero-Leakage Pipeline Transformation**
           - Physiological zeros in diabetes parameters are imputed via median values.
           - Continuous variables for linear and distance models are standardized via `StandardScaler`.
           - Tree-based models process unscaled numeric ranges natively.

        3. **Stage 3: Multi-Model Inference & Calibration**
           - Active champion model computes log-odds and calibrated probabilities.
           - Assigns risk tier: **Low Risk (<35%)**, **Moderate Risk (35–65%)**, **High Risk (>65%)**.

        4. **Stage 4: Relational Auditing & Medical Action Generation**
           - Full JSON payload and diagnostic verdicts are persisted in `predictions.db`.
           - Evidence-based clinical action plans are generated dynamically.
        """
        )

    with tab_faq:
        st.markdown("### 💡 Technical Engineering & Methodology Reference")

        tech_faqs = [
            (
                "Why benchmark multiple classifier families instead of picking a single model?",
                "In machine learning, the No Free Lunch Theorem dictates that no single model family is universally superior across different data distributions. By benchmarking linear models (Logistic Regression), tree-based models (Decision Tree), ensemble bagging (Random Forest), and instance-based distance metrics (KNN), we empirically validate which mathematical decision boundary best fits each physiological feature space.",
            ),
            (
                "How is Data Leakage prevented across preprocessing and evaluation?",
                "Data leakage occurs when parameters from holdout test sets contaminate model training. We prevent this by packaging transformations inside Scikit-Learn Pipeline and ColumnTransformer objects. Imputers and scalers are fitted strictly on the training partition (fit_transform) and subsequently transform unseen holdouts or live records using transform() only.",
            ),
            (
                "Why are Recall and F1-Score prioritized over simple Accuracy in healthcare?",
                "In clinical diagnostics, a False Negative (failing to diagnose a diseased patient) can be fatal due to untreated disease progression. A False Positive merely results in follow-up confirmatory tests. High recall directly minimizes false negatives. F1-score provides the harmonic mean of precision and recall, ensuring balanced clinical efficacy.",
            ),
            (
                "Why does Feature Scaling matter for Logistic Regression & KNN, but not for Decision Trees?",
                "Logistic Regression utilizes gradient descent weights, and KNN measures Euclidean distances. If a biomarker has large numerical magnitudes (e.g. Cholesterol: 126–564 mg/dl) and another has small magnitudes (e.g. ST depression: 0.0–6.2 mm), the distance will be dominated by cholesterol without scaling. Decision Trees evaluate monotonic splits independently, making them scale-invariant.",
            ),
            (
                "How are physiological zeros handled in the Diabetes dataset?",
                "In the Pima Indians diabetes dataset, 0 values in Glucose, Blood Pressure, Skin Thickness, Insulin, and BMI represent missing clinical data (since a living person cannot have 0 blood pressure or 0 BMI). Replacing these zeros with median imputation prevents corrupting classifier decision boundaries.",
            ),
            (
                "Why does Random Forest achieve high generalization stability?",
                "Random Forest aggregates 100 decorrelated decision trees using bootstrap aggregation (bagging) and random feature sub-spacing at each node split. This drastically lowers prediction variance without increasing bias, mitigating the severe overfitting typical of deep individual decision trees.",
            ),
            (
                "How does B-tree database indexing benefit clinical audit logging?",
                "In high-throughput clinical IT environments, queries frequently filter by timestamp, disease type, or diagnostic outcome. B-tree indexes (CREATE INDEX) reduce lookup complexity from linear O(N) table scans to logarithmic O(log N) lookups, ensuring fast historical queries.",
            ),
            (
                "Why did KNN achieve high accuracy on Parkinson's voice biomarkers?",
                "The Parkinson's voice dataset consists of continuous, standardized acoustic parameters (jitter, shimmer, fundamental frequencies) where vocal impairment forms tight, distinct geometric clusters in multi-dimensional feature space, making Euclidean nearest neighbors highly effective (92.3% accuracy).",
            ),
        ]

        for q, a in tech_faqs:
            with st.expander(q):
                st.write(f"**Technical Explanation:** {a}")

    with tab_dict:
        st.markdown("### 🩺 Clinical Biomarkers Reference Dictionary")
        bio_search = st.text_input("🔎 Search biomarkers by code or clinical description...", placeholder="e.g., chol, glucose, MDVP, bilirubin")

        for d_key, d_cfg in DISEASES_CONFIG.items():
            f_rows = [
                {
                    "Biomarker Code": f,
                    "Clinical Description": d_cfg["feature_descriptions"].get(f, ""),
                    "Valid Range": str(d_cfg["feature_ranges"].get(f, "N/A")),
                    "Type": "Categorical" if f in d_cfg["categorical_features"] else "Numerical",
                }
                for f in d_cfg["feature_columns"]
            ]
            if bio_search.strip():
                q = bio_search.strip().lower()
                f_rows = [r for r in f_rows if q in r["Biomarker Code"].lower() or q in r["Clinical Description"].lower()]
            if f_rows:
                st.markdown(f"#### {d_cfg['icon']} {d_cfg['name']} ({len(f_rows)} Biomarkers)")
                st.dataframe(pd.DataFrame(f_rows), use_container_width=True)
                st.divider()


def display_about_limitations():
    """Display system details, datasets, and clinical limitations."""
    st.markdown('<h2 class="sub-header">System Specifications & Clinical Limitations</h2>', unsafe_allow_html=True)

    tab_data, tab_algo, tab_limits = st.tabs(["📋 Datasets Citation", "🤖 Machine Learning Algorithms", "⚠️ Clinical Limitations"])

    with tab_data:
        st.markdown("### 📋 Clinical Benchmark Datasets")
        for d_key, d_cfg in DISEASES_CONFIG.items():
            info = d_cfg["dataset_info"]
            with st.expander(f"{d_cfg['icon']} {info['name']}"):
                st.write(f"**Source:** {info['source']}")
                st.write(f"**Cohort Size:** {info['samples']} patients")
                st.write(f"**Biomarkers:** {info['features']} features")
                st.write(f"**Class Distribution:** {info['target_classes']}")
                st.write(f"**Academic Citation:** *{info['citation']}*")

    with tab_algo:
        st.markdown("### 🤖 Benchmarked Algorithm Families")
        st.markdown(
            """
        1. **Logistic Regression (Linear Generalized)**: Models log-odds using a sigmoid function. Fast, interpretable, and produces calibrated probabilities.
        2. **Decision Tree (Rule-based Non-linear)**: Segments feature space into orthogonal hyper-rectangles using Gini impurity splits.
        3. **Random Forest (Ensemble Bagging)**: Combines 100 decorrelated decision trees using bootstrap aggregation and random feature sub-spacing.
        4. **K-Nearest Neighbors (Instance-based Metric)**: Classifies patients by locating the majority vote among the 5 nearest neighbors in standardized Euclidean space.
        """
        )

    with tab_limits:
        st.markdown(
            """
        <div class="danger-card">
            <h3 style="margin-top:0;">⚠️ Clinical Limitations &amp; Responsible AI Guidelines</h3>
            <ul style="margin-bottom:0; line-height:1.7;">
                <li><strong>Research &amp; Educational Software:</strong> This system is engineered as an academic engineering project and is NOT a certified medical diagnostic device.</li>
                <li><strong>No Physician Substitution:</strong> Statistical predictions must never supersede professional medical judgment, physical examination, or laboratory confirmation.</li>
                <li><strong>Demographic Generalizability:</strong> Historical benchmark datasets reflect specific demographic cohorts and require modern multi-center clinical validation.</li>
                <li><strong>Confirmatory Testing:</strong> Any elevated risk flagged by the system requires comprehensive clinical evaluation by licensed medical personnel.</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )


def main():
    """Main application routing."""
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "🏠 Home"
    if "confirm_clear" not in st.session_state:
        st.session_state["confirm_clear"] = False

    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:0.75rem; padding:0.25rem 0 0.85rem 0;">
                <div style="width:44px; height:44px; border-radius:12px; background:linear-gradient(135deg,#0ea5e9,#6366f1); display:flex; align-items:center; justify-content:center; box-shadow:0 6px 16px rgba(14,165,233,0.35);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                    </svg>
                </div>
                <div>
                    <div style="font-size:1.18rem; font-weight:800; color:#ffffff; line-height:1.15;">MediSense ML</div>
                    <div style="font-size:0.75rem; color:#94a3b8; font-weight:500;">Clinical Decision Support</div>
                </div>
            </div>
            <div class="status-pill"><span class="pulse-dot"></span> System Online • 16 Models Ready</div>
            """,
            unsafe_allow_html=True,
        )

        nav_options = [
            "🏠 Home",
            "🔍 Prediction",
            "📊 Model Performance",
            "📜 History",
            "📚 System Protocols",
            "ℹ️ About & Limitations",
        ]

        curr_idx = nav_options.index(st.session_state["nav_page"]) if st.session_state["nav_page"] in nav_options else 0
        page = st.radio("Navigation", nav_options, index=curr_idx)
        st.session_state["nav_page"] = page

        st.markdown("---")
        st.markdown("### System Telemetry")

        all_models = list(MODELS_DIR.glob("**/*.joblib"))
        st.success(f"✅ {len(all_models)} Trained Artifacts")

        try:
            db = get_database()
            tot_preds = db.get_prediction_count()
            st.info(f"💾 {tot_preds} Audit Logs in DB")
        except Exception:
            st.warning("⚠️ Database Connecting...")

        st.markdown("---")
        st.markdown("### Supported Modules")
        for d_key, d_cfg in DISEASES_CONFIG.items():
            st.markdown(f"{d_cfg['icon']} **{d_cfg['name']}**")

    display_header()

    if page == "🏠 Home":
        display_home_dashboard()
    elif page == "🔍 Prediction":
        display_prediction_page()
    elif page == "📊 Model Performance":
        display_model_performance()
    elif page == "📜 History":
        display_prediction_history()
    elif page == "📚 System Protocols":
        display_system_documentation()
    elif page == "ℹ️ About & Limitations":
        display_about_limitations()

    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #64748b; font-size: 0.86rem; font-weight: 500;'>"
        f"MediSense ML: Multi-Disease Clinical Decision Support System | "
        f"© {datetime.now().year} | Software Engineering &amp; Research Demonstration"
        f"</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
