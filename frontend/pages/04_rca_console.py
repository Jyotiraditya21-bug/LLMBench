import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from frontend.utils.ui import apply_custom_theme

load_dotenv()

BACKEND_URL = os.getenv("EVALFORGE_BACKEND_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("EVALFORGE_API_KEY", "evalforge_admin_secret_key")
HEADERS = {"X-API-Key": API_KEY}

st.set_page_config(page_title="AI Agent Console | EvalForge", layout="wide")
apply_custom_theme()

st.title("AI Agent Console")
st.subheader("Leverage intelligent agent reasoning to debug failures and generate adversarial test cases.")

st.markdown("---")


def get_completed_runs():
    try:
        r = requests.get(f"{BACKEND_URL}/evaluations", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return [run for run in r.json() if run["status"] == "COMPLETED"]
        return []
    except Exception:
        return []


def get_datasets():
    try:
        r = requests.get(f"{BACKEND_URL}/datasets", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            # Avoid showing already adversarial datasets as seeds
            return [ds for ds in r.json() if "RedTeam-Adversarial" not in ds["name"]]
        return []
    except Exception:
        return []


tab1, tab2 = st.tabs(["Root Cause Analysis (RCA)", "AI Red Team Auditor"])

with tab1:
    st.markdown("### Failure Debugger & Optimizer Agent")
    st.markdown("When prompts change or database schema updates occur, evaluation scores can degrade. Select a run to analyze failures.")
    
    completed_runs = get_completed_runs()
    
    if not completed_runs:
        st.info("No completed evaluation runs found. Run evaluations in the Evaluation Hub first.")
    else:
        selected_run = st.selectbox(
            "Select Run to Analyze",
            options=[f"Run ID: {run['id']} (Dataset ID: {run['dataset_id']}) - Accuracy: {run.get('metrics', {}).get('average_accuracy', 0.0)}" for run in completed_runs]
        )
        run_id = int(selected_run.split("Run ID: ")[-1].split(" ")[0])

        if st.button("Generate Root Cause Report"):
            with st.spinner("Agent compiling failures and synthesizing report..."):
                payload = {"run_id": run_id}
                res = requests.post(f"{BACKEND_URL}/agents/rca", headers=HEADERS, json=payload)
                
            if res.status_code == 200:
                report_data = res.json()
                st.markdown("---")
                st.markdown(report_data.get("report", ""))
            else:
                st.error(f"RCA compilation failed: {res.text}")

with tab2:
    st.markdown("### Adversarial Dataset Generator")
    st.markdown("Generate ambiguous variations, info-traps, and injection payloads to stresstest model robustness.")
    
    datasets = get_datasets()
    
    if not datasets:
        st.info("No seed datasets found. Create a dataset in the Dataset Manager first.")
    else:
        selected_ds = st.selectbox(
            "Select Seed Dataset",
            options=[f"{ds['name']} (v{ds['version']}) - ID: {ds['id']}" for ds in datasets]
        )
        dataset_id = int(selected_ds.split("ID: ")[-1])

        if st.button("Generate Adversarial Attacks"):
            with st.spinner("AI Red Team synthesising prompt variations..."):
                payload = {"dataset_id": dataset_id}
                res = requests.post(f"{BACKEND_URL}/agents/redteam", headers=HEADERS, json=payload)
                
            if res.status_code == 200:
                result_data = res.json()
                st.success(f"Adversarial Suite Created! Saved as new Dataset ID: {result_data.get('adversarial_dataset_id')} ({result_data.get('adversarial_dataset_name')})")
                
                st.markdown("#### Generated Adversarial Test Cases")
                cases_df = pd.DataFrame(result_data.get("cases", []))
                if not cases_df.empty:
                    # Flatten metadata column for visual cleanliness
                    cases_df["Attack Type"] = cases_df["meta_data"].apply(lambda x: x.get("type", "N/A"))
                    cases_df["Original Question"] = cases_df["meta_data"].apply(lambda x: x.get("original_question", "N/A"))
                    st.dataframe(cases_df[["Attack Type", "question", "ground_truth", "Original Question"]], use_container_width=True)
            else:
                st.error(f"Red Team generation failed: {res.text}")
