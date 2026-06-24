---
title: LLMBench
emoji: ⚖️
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
---

# LLMBench: LLM Evaluation and Regression Testing Platform

LLMBench is a production-grade AI quality engineering platform designed to benchmark Large Language Models, evaluate prompt templates, detect regression anomalies, and optimize LLM query costs. The platform leverages asynchronous processing queues and LLM-as-a-Judge evaluations to deliver automated engineering insights.

---

## Key Capabilities

* **Asynchronous Evaluation Pipeline:** Schedules large-scale test suites asynchronously using Celery and Redis to execute parallel runs without blocking application threads.
* **LLM-as-a-Judge (Claude Evaluation):** Leverages Claude Haiku as an automated judge to grade model responses across five qualitative dimensions: Accuracy, Completeness, Hallucination Resistance, Tone, and Reasoning.
* **Prompt Arena (A/B Testing):** Compares prompt versions side-by-side. Computes statistical latency deltas, pricing differences, and judge rating comparisons using interactive Plotly radar charts.
* **Automated Failure Diagnostics (Root Cause Agent):** Aggregates failed evaluation results and uses Claude 3.5 Sonnet to synthesize failure modes and suggest prompt scaffold corrections.
* **AI Red Team Auditor:** Analyzes target datasets to generate adversarial prompt injections, safety bypass vectors, and outdated information traps, helping test LLM robustness.
* **Cost-to-Quality Optimization:** Analyzes accuracy-to-cost efficiency frontiers and provides automated recommendations for routing queries to cheaper models (e.g. Gemini Flash) when thresholds are met.
* **CI/CD Quality Gate:** A GitHub Actions workflow runs evaluation checks on push to main, fails the build on quality regression, compiles interactive HTML dashboards, and deploys reports serverless to GitHub Pages.

---

## System Architecture

The following diagram illustrates the flow of test cases and evaluations through the platform:

```
[Developer Push / API Trigger]
             │
             ▼
      [FastAPI Backend] ──(Creates Run)──► [PostgreSQL DB]
             │
      (Publishes Job)
             │
             ▼
       [Redis Queue]
             │
      (Pulls Task)
             │
             ▼
     [Celery Workers] ◄──(Executes Test Cases)──► [Target LLM APIs]
             │
      (Grades Output)
             │
             ▼
   [Claude-as-a-Judge] ──(Saves Results)──► [PostgreSQL DB]
                                                 │
                                           (Compiles HTML)
                                                 │
                                                 ▼
                                        [GitHub Pages Report]
```

---

## Tech Stack & Standards

* **Backend:** FastAPI, SQLAlchemy 2.0 (Async), Pydantic V2, Alembic
* **Background Processing:** Celery, Redis
* **Database:** PostgreSQL (with SQLite fallback support)
* **Frontend Showcase:** Vanilla HTML5, CSS3, JavaScript (ES6), Plotly.js
* **Testing:** Pytest, pytest-asyncio, pytest-mock

---

## Local Setup

Follow these steps to run the complete platform services locally:

### 1. Launch Services via Docker Compose
Initialize the PostgreSQL, Redis, Celery, and FastAPI application containers:
```bash
docker-compose up -d
```

### 2. Set Up Python Environment
Create a virtual environment and install the required dependencies:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Seed the Database
Initialize tables and populate mock datasets:
```bash
python -m backend.app.core.seed_db
```

### 4. Run the Servers Locally (Outside Docker)
If you prefer running the backend and worker processes directly in your terminal:
* **Web API Server:**
  ```bash
  uvicorn backend.app.main:app --reload --port 8000
  ```
* **Celery Worker:**
  ```bash
  celery -A backend.app.core.celery_app worker --pool=solo --loglevel=info
  ```

### 5. Run the Automated Tests
Verify code behavior and endpoint security checks:
```bash
PYTHONPATH=. pytest
```

---

## Performance & Cost Metrics

The following metrics represent baseline results collected during local benchmark runs:

* **Average Query Latency:** 450ms - 505ms per API response.
* **Average Instance Query Cost:** $0.00036 USD per query.
* **Accuracy Score Range:** 4.0 - 4.5 out of 5.0 (graded by Claude-as-a-Judge).
* **Measured Hallucination Rate:** 0.0% under standard reasoning test suites.
