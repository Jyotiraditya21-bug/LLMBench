import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from frontend.utils.ui import apply_custom_theme, style_plotly_fig

load_dotenv()

# --- Config Settings ---
BACKEND_URL = os.getenv("EVALFORGE_BACKEND_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("EVALFORGE_API_KEY", "evalforge_admin_secret_key")
HEADERS = {"X-API-Key": API_KEY}

# --- Streamlit Layout ---
st.set_page_config(
    page_title="EvalForge | AI Quality Engineering Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Apply custom Forest Green theme ---
apply_custom_theme()


def get_data(endpoint: str):
    """Utility to pull data from backend APIs safely."""
    try:
        r = requests.get(f"{BACKEND_URL}/{endpoint}", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


st.title("EvalForge")
st.subheader("LLM Evaluation, Regression Testing & AI Quality Monitoring Platform")

st.markdown("---")

# --- KPI Section ---
datasets = get_data("datasets")
prompts = get_data("prompts")
runs = get_data("evaluations")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Datasets", value=len(datasets))
with col2:
    st.metric(label="Prompt Templates", value=len(prompts))
with col3:
    completed_runs = [r for r in runs if r.get("status") == "COMPLETED"]
    st.metric(label="Evaluation Runs", value=len(runs), delta=f"{len(completed_runs)} completed")
with col4:
    total_spent = sum([r.get("metrics", {}).get("total_cost", 0.0) for r in completed_runs])
    st.metric(label="Total Spent (USD)", value=f"${total_spent:.4f}")

st.markdown("### LLM Cost-to-Quality Efficiency Frontier")

# Generate standard data representing modern models if no active runs exist
frontier_data = []
if completed_runs:
    for run in completed_runs:
        metrics = run.get("metrics", {})
        results = run.get("results", [])
        if results:
            # Group by model
            models_run = set([res.get("model_name") for res in results])
            for m in models_run:
                m_results = [res for res in results if res.get("model_name") == m]
                avg_acc = sum([r.get("accuracy", 0.0) for r in m_results]) / len(m_results)
                avg_cost = sum([r.get("cost", 0.0) for r in m_results]) / len(m_results)
                avg_lat = sum([r.get("latency_ms", 0.0) for r in m_results]) / len(m_results)
                frontier_data.append({
                    "Model": m,
                    "Average Accuracy (1-5)": round(avg_acc, 2),
                    "Average Cost ($)": round(avg_cost, 6),
                    "Latency (ms)": round(avg_lat, 2)
                })

# Fallback defaults for visualization
if not frontier_data:
    frontier_data = [
        {"Model": "gpt-4o", "Average Accuracy (1-5)": 4.75, "Average Cost ($)": 0.0125, "Latency (ms)": 1250.0},
        {"Model": "claude-3-5-sonnet", "Average Accuracy (1-5)": 4.82, "Average Cost ($)": 0.0095, "Latency (ms)": 1500.0},
        {"Model": "gemini-1.5-flash", "Average Accuracy (1-5)": 4.10, "Average Cost ($)": 0.0003, "Latency (ms)": 650.0},
        {"Model": "gemini-1.5-pro", "Average Accuracy (1-5)": 4.60, "Average Cost ($)": 0.0045, "Latency (ms)": 1900.0},
    ]

df_frontier = pd.DataFrame(frontier_data)
fig = px.scatter(
    df_frontier,
    x="Average Cost ($)",
    y="Average Accuracy (1-5)",
    size="Latency (ms)",
    color="Model",
    hover_name="Model",
    log_x=True,
    title="Quality vs. Cost Scale (Bubble Size = Latency)",
    color_discrete_sequence=px.colors.qualitative.G10
)
fig = style_plotly_fig(fig)
st.plotly_chart(fig, use_container_width=True)

# --- Recent Runs Table ---
st.markdown("### Recent Evaluation Runs")
if runs:
    run_rows = []
    for r in runs[:5]:
        metrics = r.get("metrics", {})
        run_rows.append({
            "Run ID": r.get("id"),
            "Dataset ID": r.get("dataset_id"),
            "Prompt ID": r.get("prompt_id"),
            "Status": r.get("status"),
            "Accuracy": metrics.get("average_accuracy", "N/A"),
            "Hallucination Rate": metrics.get("hallucination_rate", "N/A"),
            "Cost ($)": metrics.get("total_cost", "N/A"),
            "Timestamp": r.get("created_at")
        })
    st.table(pd.DataFrame(run_rows))
else:
    st.info("No evaluation runs recorded yet. Head over to the Evaluation Hub to trigger a run.")
