import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import json
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from frontend.utils.ui import apply_custom_theme

load_dotenv()

BACKEND_URL = os.getenv("EVALFORGE_BACKEND_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("EVALFORGE_API_KEY", "evalforge_admin_secret_key")
HEADERS = {"X-API-Key": API_KEY}

st.set_page_config(page_title="Dataset Management | EvalForge", layout="wide")
apply_custom_theme()

st.title("Dataset Management")
st.subheader("Manage evaluation test suites, categories, and test cases.")

st.markdown("---")


def get_datasets():
    try:
        r = requests.get(f"{BACKEND_URL}/datasets", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception as e:
        st.error(f"Failed to connect to backend: {str(e)}")
        return []


# --- Create Dataset Form ---
with st.expander("Create New Dataset", expanded=False):
    with st.form("create_dataset_form"):
        name = st.text_input("Dataset Name", placeholder="e.g. Customer Support Core QA")
        version = st.text_input("Version", value="1.0.0", placeholder="e.g. 1.0.0")
        description = st.text_area("Description", placeholder="Enter dataset goals or source notes...")
        category = st.selectbox(
            "Primary Evaluation Domain",
            ["factual", "reasoning", "hallucination", "tone", "safety", "adversarial", "rag"]
        )
        
        submitted = st.form_submit_key = st.form_submit_button("Create Dataset")
        if submitted:
            if not name:
                st.error("Dataset name is required.")
            else:
                payload = {
                    "name": name,
                    "version": version,
                    "description": description,
                    "category": category
                }
                res = requests.post(f"{BACKEND_URL}/datasets/", headers=HEADERS, json=payload)
                if res.status_code == 201:
                    st.success(f"Dataset '{name}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"Error creating dataset: {res.text}")

# --- Load Datasets ---
datasets = get_datasets()

if not datasets:
    st.info("No datasets registered yet. Use the panel above to create your first dataset.")
else:
    # Select dataset to inspect
    selected_ds_name = st.selectbox(
        "Select Dataset to Inspect / Manage",
        options=[f"{ds['name']} (v{ds['version']}) - ID: {ds['id']}" for ds in datasets]
    )
    
    # Extract selected ID
    selected_ds_id = int(selected_ds_name.split("ID: ")[-1])
    selected_ds = next(ds for ds in datasets if ds["id"] == selected_ds_id)

    st.markdown(f"### Dataset Details: {selected_ds['name']}")
    st.write(f"**Version:** {selected_ds['version']} | **Category:** {selected_ds['category']}")
    st.write(f"**Description:** {selected_ds['description'] or 'No description provided.'}")

    # Add Test Cases Tab and Upload Tab
    tab1, tab2, tab3 = st.tabs(["Test Cases List", "Batch Upload JSON", "Add Single Case"])

    with tab1:
        # Load test cases
        tc_res = requests.get(f"{BACKEND_URL}/datasets/{selected_ds_id}/testcases", headers=HEADERS)
        if tc_res.status_code == 200:
            test_cases = tc_res.json()
            if test_cases:
                tc_df = pd.DataFrame(test_cases)
                # Drop formatting columns for layout cleanliness
                display_df = tc_df[["id", "category", "question", "ground_truth", "meta_data"]]
                st.dataframe(display_df, use_container_width=True)
                
                # Delete Test Case
                tc_to_delete = st.selectbox("Select Test Case ID to Delete", options=[tc["id"] for tc in test_cases])
                if st.button("Delete Selected Test Case"):
                    del_res = requests.delete(f"{BACKEND_URL}/datasets/{selected_ds_id}/testcases/{tc_to_delete}", headers=HEADERS)
                    if del_res.status_code == 200:
                        st.success(f"Test case {tc_to_delete} deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete test case.")
            else:
                st.info("This dataset has no test cases yet.")
        else:
            st.error("Failed to load test cases.")

    with tab2:
        st.markdown("#### Upload JSON Test Cases Array")
        st.code("""
[
  {
    "question": "What is diabetes?",
    "ground_truth": "Diabetes is a chronic disease where the body cannot regulate glucose...",
    "category": "factual",
    "meta_data": {"difficulty": "easy"}
  }
]
        """, language="json")
        
        uploaded_file = st.file_uploader("Choose a JSON file containing test cases list", type="json")
        if uploaded_file is not None:
            try:
                tc_data = json.load(uploaded_file)
                if not isinstance(tc_data, list):
                    st.error("JSON file must contain a list of test case objects.")
                else:
                    if st.button("Upload and Save Batch"):
                        upload_res = requests.post(
                            f"{BACKEND_URL}/datasets/{selected_ds_id}/testcases/batch",
                            headers=HEADERS,
                            json=tc_data
                        )
                        if upload_res.status_code == 201:
                            st.success(f"Batch imported successfully! {upload_res.json().get('message', '')}")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {upload_res.text}")
            except Exception as ex:
                st.error(f"Error parsing JSON: {str(ex)}")

    with tab3:
        st.markdown("#### Append Single Test Case")
        with st.form("single_testcase_form"):
            question = st.text_area("Question / Input Prompt", placeholder="e.g. Write a brief history of AI.")
            ground_truth = st.text_area("Ground Truth / Expected Output", placeholder="e.g. Artificial Intelligence started in the 1950s with Alan Turing...")
            category = st.text_input("TestCase Category Tag", value=selected_ds["category"])
            metadata_str = st.text_area("Metadata (JSON dict)", value="{}")

            submitted_tc = st.form_submit_button("Save Test Case")
            if submitted_tc:
                if not question or not ground_truth:
                    st.error("Question and Ground Truth are required.")
                else:
                    try:
                        meta = json.loads(metadata_str) if metadata_str else {}
                        tc_payload = {
                            "question": question,
                            "ground_truth": ground_truth,
                            "category": category,
                            "meta_data": meta
                        }
                        res = requests.post(f"{BACKEND_URL}/datasets/{selected_ds_id}/testcases", headers=HEADERS, json=tc_payload)
                        if res.status_code == 201:
                            st.success("Test case saved successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error saving: {res.text}")
                    except Exception as e:
                        st.error(f"Invalid Metadata JSON format: {str(e)}")
