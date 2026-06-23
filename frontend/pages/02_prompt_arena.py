import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from frontend.utils.ui import apply_custom_theme, style_plotly_fig

load_dotenv()

BACKEND_URL = os.getenv("EVALFORGE_BACKEND_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("EVALFORGE_API_KEY", "evalforge_admin_secret_key")
HEADERS = {"X-API-Key": API_KEY}

st.set_page_config(page_title="Prompt Arena | EvalForge", layout="wide")
apply_custom_theme()

st.title("Prompt Arena & Benchmark")
st.subheader("Compare prompt templates and rank versions by accuracy, latency, and cost.")

st.markdown("---")


def get_prompts():
    try:
        r = requests.get(f"{BACKEND_URL}/prompts", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


def get_evaluation_runs():
    try:
        r = requests.get(f"{BACKEND_URL}/evaluations", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


# --- Create Prompt Template ---
with st.expander("Register Prompt Template Version", expanded=False):
    with st.form("create_prompt_form"):
        name = st.text_input("Template Name", placeholder="e.g. Reasoning Scaffold Prompt")
        version = st.text_input("Version Tag", placeholder="e.g. V1.0")
        system_prompt = st.text_area("System Instruction Context", placeholder="e.g. You are a helpful assistant...")
        user_template = st.text_area("User Template Text", placeholder="Answer the question: {{question}}")
        description = st.text_input("Release Notes", placeholder="What changed in this template?")

        submitted = st.form_submit_button("Register Template")
        if submitted:
            if not name or not version or not user_template:
                st.error("Name, version, and user template are required.")
            else:
                payload = {
                    "name": name,
                    "version": version,
                    "system_prompt": system_prompt,
                    "user_template": user_template,
                    "description": description
                }
                res = requests.post(f"{BACKEND_URL}/prompts/", headers=HEADERS, json=payload)
                if res.status_code == 201:
                    st.success(f"Prompt '{name}' version '{version}' registered!")
                    st.rerun()
                else:
                    st.error(f"Failed to register prompt: {res.text}")

prompts = get_prompts()
runs = get_evaluation_runs()

if not prompts:
    st.info("No prompt templates registered yet. Use the panel above to add one.")
else:
    # Get unique prompt names
    prompt_names = list(set([p["name"] for p in prompts]))
    
    st.markdown("### Prompt Arena Comparison Playground")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_prompt_name = st.selectbox("Select Prompt Template Group", options=prompt_names)
        available_versions = [p for p in prompts if p["name"] == selected_prompt_name]
    
    with col2:
        baseline_v = st.selectbox("Select Baseline Version (A)", options=[p["version"] for p in available_versions])
        baseline_prompt = next(p for p in available_versions if p["version"] == baseline_v)
        
    with col3:
        comp_v = st.selectbox("Select Comparison Version (B)", options=[v for v in [p["version"] for p in available_versions] if v != baseline_v], index=0 if len(available_versions) > 1 else None)
        comp_prompt = next(p for p in available_versions if p["version"] == comp_v) if comp_v else None

    if not comp_prompt:
        st.warning("Please register at least two versions of this prompt to perform comparisons.")
    else:
        # Show prompt comparisons side-by-side
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.info(f"**Baseline Prompt (A) - {baseline_v}**")
            st.markdown(f"**System Prompt:**\n`{baseline_prompt['system_prompt'] or 'None'}`")
            st.markdown(f"**User Template:**\n`{baseline_prompt['user_template']}`")
        with p_col2:
            st.info(f"**Comparison Prompt (B) - {comp_v}**")
            st.markdown(f"**System Prompt:**\n`{comp_prompt['system_prompt'] or 'None'}`")
            st.markdown(f"**User Template:**\n`{comp_prompt['user_template']}`")

        st.markdown("### Regression Check & Deltas")
        
        # Search for runs that evaluated these prompts
        base_runs = [r for r in runs if r.get("prompt_id") == baseline_prompt["id"] and r.get("status") == "COMPLETED"]
        comp_runs = [r for r in runs if r.get("prompt_id") == comp_prompt["id"] and r.get("status") == "COMPLETED"]
        
        if not base_runs or not comp_runs:
            st.warning("No evaluation runs matching both of these prompt versions are recorded. Run the benchmarks in the 'Evaluation Hub' first.")
        else:
            # Dropdowns to select which specific run to compare
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                selected_base_run = st.selectbox(
                    f"Select Run for Baseline (A) - {baseline_v}",
                    options=[f"Run ID: {r['id']} (Dataset ID: {r['dataset_id']}) - Score: {r.get('metrics', {}).get('average_accuracy', 0.0)}" for r in base_runs]
                )
                base_run_id = int(selected_base_run.split("Run ID: ")[-1].split(" ")[0])
                
            with r_col2:
                selected_comp_run = st.selectbox(
                    f"Select Run for Comparison (B) - {comp_v}",
                    options=[f"Run ID: {r['id']} (Dataset ID: {r['dataset_id']}) - Score: {r.get('metrics', {}).get('average_accuracy', 0.0)}" for r in comp_runs]
                )
                comp_run_id = int(selected_comp_run.split("Run ID: ")[-1].split(" ")[0])

            if st.button("Trigger Regression Analysis Report"):
                payload = {
                    "baseline_run_id": base_run_id,
                    "comparison_run_id": comp_run_id
                }
                res = requests.post(f"{BACKEND_URL}/evaluations/compare", headers=HEADERS, json=payload)
                if res.status_code == 201:
                    report = res.json()
                    findings = report.get("findings", {})
                    
                    st.success("Regression report generated successfully!")
                    
                    # Columns to show comparisons
                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    
                    # Score Delta
                    score_delta = report.get("score_delta", 0.0)
                    delta_color = "normal" if score_delta >= 0 else "inverse"
                    kpi1.metric(
                        label="Average Accuracy Delta",
                        value=f"{score_delta:+.2f}",
                        delta=f"Baseline: {findings.get('baseline_accuracy', 0.0)}",
                        delta_color=delta_color
                    )
                    
                    # Latency Delta
                    lat_delta = findings.get("latency_delta_ms", 0.0)
                    kpi2.metric(
                        label="Avg Latency Delta",
                        value=f"{lat_delta:+.1f} ms",
                        delta="Lower is better",
                        delta_color="inverse"
                    )
                    
                    # Cost Delta
                    cost_delta = findings.get("cost_delta", 0.0)
                    kpi3.metric(
                        label="Cost Delta",
                        value=f"${cost_delta:+.5f}",
                        delta="Lower is better",
                        delta_color="inverse"
                    )
                    
                    # Hallucination Rate
                    hall_delta = findings.get("hallucination_rate_delta", 0.0)
                    kpi4.metric(
                        label="Hallucination Rate Delta",
                        value=f"{hall_delta:+.2%}",
                        delta="Lower is better",
                        delta_color="inverse"
                    )
                    
                    # Plotly chart comparison
                    base_run_obj = next(r for r in base_runs if r["id"] == base_run_id)
                    comp_run_obj = next(r for r in comp_runs if r["id"] == comp_run_id)
                    
                    m_base = base_run_obj.get("metrics", {})
                    m_comp = comp_run_obj.get("metrics", {})
                    
                    categories = ["Accuracy", "Completeness", "Hallucination Resistance", "Tone", "Reasoning"]
                    base_scores = [
                        m_base.get("average_accuracy", 0.0),
                        m_base.get("average_completeness", 0.0),
                        m_base.get("average_hallucination", 0.0),
                        m_base.get("average_tone", 0.0),
                        m_base.get("average_reasoning", 0.0)
                    ]
                    comp_scores = [
                        m_comp.get("average_accuracy", 0.0),
                        m_comp.get("average_completeness", 0.0),
                        m_comp.get("average_hallucination", 0.0),
                        m_comp.get("average_tone", 0.0),
                        m_comp.get("average_reasoning", 0.0)
                    ]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=base_scores,
                        theta=categories,
                        fill='toself',
                        name=f"Baseline ({baseline_v})",
                        line_color="#E7EFE4",
                        fillcolor="rgba(231, 255, 228, 0.15)"
                    ))
                    fig.add_trace(go.Scatterpolar(
                        r=comp_scores,
                        theta=categories,
                        fill='toself',
                        name=f"Comparison ({comp_v})",
                        line_color="#98CBB0",
                        fillcolor="rgba(152, 203, 176, 0.3)"
                    ))
                    fig = style_plotly_fig(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Failed to compile regression report.")
