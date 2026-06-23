# Phase 5: Streamlit Frontend Dashboard

This document details the development and structure of the **EvalForge** user interface and visual dashboards built during Phase 5.

---

## 1. Summary of Files Created

1. **[frontend/requirements.txt](file:///Users/jimmycodes/LLMBench/frontend/requirements.txt):** Lists frontend dependencies including Streamlit, Plotly, and pandas.
2. **[frontend/app.py](file:///Users/jimmycodes/LLMBench/frontend/app.py):** Main landing portal containing aggregated KPIs (cost, latency, runs) and the cost-to-performance efficiency scatter chart.
3. **[frontend/pages/01_datasets.py](file:///Users/jimmycodes/LLMBench/frontend/pages/01_datasets.py):** UI for creating datasets, uploading JSON arrays of test cases in bulk, and review test sheets.
4. **[frontend/pages/02_prompt_arena.py](file:///Users/jimmycodes/LLMBench/frontend/pages/02_prompt_arena.py):** UI for registering prompts and comparing versions side-by-side using dynamic radar chart dimension views.
5. **[frontend/pages/03_eval_hub.py](file:///Users/jimmycodes/LLMBench/frontend/pages/03_eval_hub.py):** UI for configuring evaluations, triggering backend task schedules, and monitoring running pipelines using active polling.

---

## 2. Core Code Section Explanations

### Cost-to-Quality Scatter Chart (Plotly)
```python
fig = px.scatter(
    df_frontier,
    x="Average Cost ($)",
    y="Average Accuracy (1-5)",
    size="Latency (ms)",
    color="Model",
    log_x=True,
    ...
)
```
- **Like I am 5 years old 🧸:** Think of this chart like a graph of candy in a store. On the bottom, we see how much the candy costs. On the side, we see how yummy it is. The size of the bubble shows how long it takes to chew. We want candy that is high up (very yummy) and far to the left (very cheap)!
- **Industry Relevance 🚀:** A key part of LLMOps is deciding which model to use. GPT-4o might be very accurate, but costing 100x more than Gemini Flash makes Flash the better choice for simple operations. Mapping this tradeoff on a scatter plot helps product teams choose models visually.
- **Interview Relevance 🎤:** *How do you demonstrate cost-vs-quality trade-offs in an LLM benchmark dashboard?* By generating a log-scale scatter plot (Plotly/Matplotlib) mapping the cost on the X-axis (since cost varies exponentially between models) and the accuracy score on the Y-axis. Using bubble size to represent latency adds a third dimension, revealing the "efficiency frontier" of available models.

---

### Real-Time Pipeline Status Polling
```python
for i in range(1, 100):
    poll_res = requests.get(f"{BACKEND_URL}/evaluations/{run_id}", headers=HEADERS)
    if poll_res.status_code == 200:
        current_run = poll_res.json()
        status = current_run["status"]
        if status == "COMPLETED":
            ...
            break
        time.sleep(1)
```
- **Like I am 5 years old 🧸:** When you ask "Are we there yet?" in the car, you ask every few minutes. That is what this code does. It keeps calling the backend server every second to check if the background worker is finished grading the homework.
- **Industry Relevance 🚀:** Since evaluation loops run in the background (via Celery), the frontend needs to retrieve updates asynchronously. Active polling is a simple, robust way to show real-time progress without the complexity of WebSockets.
- **Interview Relevance 🎤:** *How does your frontend show updates for background-triggered tasks?* The frontend triggers the run asynchronously, receiving a task ID immediately (HTTP 202). It then starts a loop to query (poll) the status endpoint. Once the status transitions from `PENDING` or `RUNNING` to `COMPLETED` or `FAILED`, the loop breaks, and results are loaded.
