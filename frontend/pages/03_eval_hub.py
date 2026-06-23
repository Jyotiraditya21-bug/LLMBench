import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import time
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from frontend.utils.ui import apply_custom_theme

load_dotenv()

BACKEND_URL = os.getenv("EVALFORGE_BACKEND_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("EVALFORGE_API_KEY", "evalforge_admin_secret_key")
HEADERS = {"X-API-Key": API_KEY}

st.set_page_config(page_title="Evaluation Hub | EvalForge", layout="wide")
apply_custom_theme()

st.title("Evaluation Hub & Pipeline")
st.subheader("Schedule evaluation runs, monitor real-time execution, and inspect historical logs.")

st.markdown("---")


def get_datasets():
    try:
        r = requests.get(f"{BACKEND_URL}/datasets", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


def get_prompts():
    try:
        r = requests.get(f"{BACKEND_URL}/prompts", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


def get_runs():
    try:
        r = requests.get(f"{BACKEND_URL}/evaluations", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


datasets = get_datasets()
prompts = get_prompts()

tab1, tab2 = st.tabs(["Trigger New Evaluation Run", "Historical Execution Logs"])

with tab1:
    st.markdown("### Run Configurations")
    
    if not datasets:
        st.warning("Please create a dataset before triggering evaluations.")
    else:
        # Form inputs
        selected_ds_name = st.selectbox(
            "Select Evaluation Dataset",
            options=[f"{ds['name']} (v{ds['version']}) - ID: {ds['id']}" for ds in datasets],
            key="eval_ds"
        )
        selected_ds_id = int(selected_ds_name.split("ID: ")[-1])
        
        prompt_options = ["None (Send raw questions directly)"] + [f"{p['name']} (v{p['version']}) - ID: {p['id']}" for p in prompts]
        selected_p_name = st.selectbox("Select Prompt Template (Optional)", options=prompt_options)
        
        selected_prompt_id = None
        if selected_p_name != "None (Send raw questions directly)":
            selected_prompt_id = int(selected_p_name.split("ID: ")[-1])

        selected_models = st.multiselect(
            "Select LLM Model Providers Suite",
            options=["gpt-4o", "gpt-3.5-turbo", "claude-3-5-sonnet", "claude-3-haiku", "gemini-1.5-flash", "gemini-1.5-pro"],
            default=["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-flash"]
        )

        if st.button("Start Evaluation Suite"):
            if not selected_models:
                st.error("Please select at least one model to evaluate.")
            else:
                payload = {
                    "dataset_id": selected_ds_id,
                    "prompt_id": selected_prompt_id,
                    "models": selected_models
                }
                
                with st.spinner("Initializing evaluation pipeline..."):
                    res = requests.post(f"{BACKEND_URL}/evaluations/trigger", headers=HEADERS, json=payload)
                    
                if res.status_code == 202:
                    run_data = res.json()
                    run_id = run_data["id"]
                    
                    st.success(f"Evaluation Run ID {run_id} started successfully!")
                    
                    # Start dynamic status tracker polling
                    status_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    
                    # Since mock runs or background runs take a few seconds:
                    for i in range(1, 100):
                        poll_res = requests.get(f"{BACKEND_URL}/evaluations/{run_id}", headers=HEADERS)
                        if poll_res.status_code == 200:
                            current_run = poll_res.json()
                            status = current_run["status"]
                            status_placeholder.info(f"Current Pipeline Run Status: **{status}**")
                            
                            if status == "COMPLETED":
                                progress_bar.progress(100)
                                st.success("Pipeline evaluation complete! Head over to the history logs to inspect output metrics.")
                                st.balloons()
                                break
                            elif status == "FAILED":
                                progress_bar.progress(100)
                                st.error(f"Run failed: {current_run.get('metrics', {}).get('error', 'Unknown fault.')}")
                                break
                            
                            progress_bar.progress(min(i * 10, 95))
                            time.sleep(1)
                else:
                    st.error(f"Failed to start evaluation suite: {res.text}")

with tab2:
    st.markdown("### Historical Execution Logs")
    runs = get_runs()
    
    if not runs:
        st.info("No runs found in database registry.")
    else:
        selected_run_name = st.selectbox(
            "Select Evaluation Run to Inspect",
            options=[f"Run ID: {r['id']} (Dataset ID: {r['dataset_id']}) - Status: {r['status']}" for r in runs]
        )
        selected_run_id = int(selected_run_name.split("Run ID: ")[-1].split(" ")[0])
        
        # Pull detailed run details
        run_res = requests.get(f"{BACKEND_URL}/evaluations/{selected_run_id}", headers=HEADERS)
        if run_res.status_code == 200:
            run_details = run_res.json()
            
            st.markdown(f"#### Run Metadata — Status: **{run_details['status']}**")
            st.write(f"**Created At:** {run_details['created_at']}")
            
            # Display KPIs if completed
            if run_details["status"] == "COMPLETED":
                metrics = run_details.get("metrics", {})
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(label="Average Accuracy (1-5)", value=metrics.get("average_accuracy", "N/A"))
                with col2:
                    st.metric(label="Hallucination Rate (%)", value=f"{metrics.get('hallucination_rate', 0.0):.2%}")
                with col3:
                    st.metric(label="Avg Latency (ms)", value=f"{metrics.get('average_latency_ms', 0.0)} ms")
                with col4:
                    st.metric(label="Total Cost (USD)", value=f"${metrics.get('total_cost', 0.0):.5f}")
                    
                # Nested test case results table
                st.markdown("#### Granular Test Results")
                results = run_details.get("results", [])
                if results:
                    flat_results = []
                    for res in results:
                        tc = res.get("test_case", {})
                        flat_results.append({
                            "TestCase ID": res.get("test_case_id"),
                            "Model": res.get("model_name"),
                            "Question": tc.get("question", "N/A"),
                            "Ground Truth": tc.get("ground_truth", "N/A"),
                            "Model Output": res.get("raw_output"),
                            "Accuracy": res.get("accuracy"),
                            "Completeness": res.get("completeness"),
                            "Hallucination": res.get("hallucination"),
                            "Reasoning": res.get("reasoning"),
                            "Judge Explanation": res.get("reason"),
                            "Latency (ms)": res.get("latency_ms"),
                            "Cost ($)": res.get("cost")
                        })
                    st.dataframe(pd.DataFrame(flat_results), use_container_width=True)
                else:
                    st.info("No granular results found for this run.")
            else:
                st.info("Evaluation run is either pending, running, or failed. Awaiting status transition.")
