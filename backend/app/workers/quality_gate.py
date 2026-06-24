import os
import sys
import time
import requests

# Load configs from env
BACKEND_URL = os.getenv("EVALFORGE_BACKEND_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("EVALFORGE_API_KEY", "evalforge_admin_secret_key")
HEADERS = {"X-API-Key": API_KEY}

DATASET_ID = int(os.getenv("EVALFORGE_DATASET_ID", "1"))
BASELINE_RUN_ID = int(os.getenv("EVALFORGE_BASELINE_RUN_ID", "1"))
PROMPT_ID = int(os.getenv("EVALFORGE_PROMPT_ID", "1"))
TARGET_MODELS = os.getenv("EVALFORGE_MODELS", "claude-3-haiku").split(",")

# Threshold boundary to fail the CI build
ACCURACY_DROP_THRESHOLD = -1.0


def check_quality_gate():
    print("[INFO] Triggering AI Quality Gate Benchmark Evaluation...")
    
    # 1. Trigger evaluation run
    trigger_payload = {
        "dataset_id": DATASET_ID,
        "prompt_id": PROMPT_ID,
        "models": TARGET_MODELS
    }
    
    res = requests.post(f"{BACKEND_URL}/evaluations/trigger", headers=HEADERS, json=trigger_payload)
    if res.status_code != 202:
        print(f"[ERROR] Failed to trigger evaluation run: {res.text}")
        sys.exit(1)
        
    run_data = res.json()
    run_id = run_data["id"]
    print(f"[SUCCESS] Evaluation run triggered successfully. Run ID: {run_id}")

    # 2. Poll until completed
    while True:
        poll_res = requests.get(f"{BACKEND_URL}/evaluations/{run_id}", headers=HEADERS)
        if poll_res.status_code != 200:
            print("[ERROR] Failed to query run status. Aborting.")
            sys.exit(1)
            
        run = poll_res.json()
        status = run["status"]
        print(f"... Current run status: {status}")
        
        if status == "COMPLETED":
            break
        elif status == "FAILED":
            print(f"[ERROR] Evaluation run failed. Error: {run.get('metrics', {}).get('error')}")
            sys.exit(1)
            
        time.sleep(2)

    # 3. Trigger regression comparison
    print(f"[INFO] Comparing Target Run {run_id} to Baseline Run {BASELINE_RUN_ID}...")
    compare_payload = {
        "baseline_run_id": BASELINE_RUN_ID,
        "comparison_run_id": run_id
    }
    
    comp_res = requests.post(f"{BACKEND_URL}/evaluations/compare", headers=HEADERS, json=compare_payload)
    if comp_res.status_code != 201:
        print(f"[ERROR] Regression comparison failed: {comp_res.text}")
        sys.exit(1)
        
    report = comp_res.json()
    score_delta = report.get("score_delta", 0.0)
    findings = report.get("findings", {})
    
    print("\n--- AI Quality Gate Findings Summary ---")
    print(f"Baseline Average Accuracy: {findings.get('baseline_accuracy', 0.0)}")
    print(f"Comparison Average Accuracy: {findings.get('comparison_accuracy', 0.0)}")
    print(f"Accuracy Delta: {score_delta:+.2f}")
    print(f"Latency Delta: {findings.get('latency_delta_ms', 0.0):+.1f} ms")
    print(f"Cost Delta: ${findings.get('cost_delta', 0.0):+.5f}")
    
    # 4. Enforce quality checks
    if score_delta <= ACCURACY_DROP_THRESHOLD:
        print(f"\n[FAIL] QUALITY GATE FAILED: Score degradation ({score_delta:+.2f}) exceeds the limit of {ACCURACY_DROP_THRESHOLD}.")
        sys.exit(1)
    else:
        print(f"\n[PASS] QUALITY GATE PASSED: Performance remains within acceptable thresholds.")
        sys.exit(0)


if __name__ == "__main__":
    check_quality_gate()
