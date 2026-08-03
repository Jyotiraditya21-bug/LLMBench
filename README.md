
# LLMBench: LLM Evaluation and Regression Testing Platform
https://jyotiraditya21-bug.github.io/LLMBench/

LLMBench is a production-grade AI quality engineering platform designed to benchmark Large Language Models, evaluate prompt templates, detect regression anomalies, and optimize LLM query costs. The platform leverages asynchronous processing queues and LLM-as-a-Judge evaluations to deliver automated engineering insights.

---

## Key Capabilities

* **Asynchronous Evaluation Pipeline:** Schedules immutable evaluation snapshots through Celery and Redis, with bounded model concurrency and provider-specific limits.
* **LLM-as-a-Judge (Claude Evaluation):** Leverages Claude Haiku as an automated judge to grade model responses across five qualitative dimensions: Accuracy, Completeness, Hallucination Resistance, Tone, and Reasoning.
* **Prompt Arena (A/B Testing):** Compares prompt versions side-by-side. Computes statistical latency deltas, pricing differences, and judge rating comparisons using interactive Plotly radar charts.
* **Automated Failure Diagnostics (Root Cause Agent):** Aggregates failed evaluation results and uses Claude 3.5 Sonnet to synthesize failure modes and suggest prompt scaffold corrections.
* **AI Red Team Auditor:** Analyzes target datasets to generate adversarial prompt injections, safety bypass vectors, and outdated information traps, helping test LLM robustness.
* **Cost-to-Quality Optimization:** Analyzes accuracy-to-cost efficiency frontiers and provides automated recommendations for routing queries to cheaper models (e.g. Gemini Flash) when thresholds are met.
* **CI Verification:** GitHub Actions runs the automated test suite on pushes and pull requests. A live LLM quality gate will be restored in Version 2 after persistent real baselines are implemented.
* **Strict Validation:** Rejects unsupported or duplicate models, malformed IDs, unknown request fields, invalid numeric metrics, and out-of-range judge scores.
* **Reliable Evaluation Jobs:** Records queue failures, publishes progress, applies bounded provider timeouts and worker retries, supports cancellation, and prevents duplicate result rows.
* **Reproducible History:** Captures dataset, test-case, prompt, model, judge, and pricing versions for every run and rejects incompatible regression comparisons.
* **Operational Readiness:** Provides database, Redis, and worker readiness checks, request IDs, structured request logs, pinned dependencies, and automated security auditing.

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

Create a strong API key before starting any service. The application has no
built-in default credential:

```bash
export EVALFORGE_API_KEY="$(openssl rand -hex 32)"
```

Enter this value when the dashboard asks for the API key. It is kept only in
the current browser session.

Real evaluation mode never substitutes fake results when a provider is missing
or fails. For UI demonstrations without provider credentials, explicitly set
`DEMO_MODE=true`. Demo runs are labeled `DEMO_COMPLETED` and are excluded from
production regression, cost, and quality-gate results.

Evaluation workers retry transient failures twice with exponential backoff.
Each provider or judge call is limited to 120 seconds, while a complete task has
a 30-minute soft limit. Queued or active runs can be cancelled with
`POST /api/v1/evaluations/{run_id}/cancel`.

### 1. Launch Services via Docker Compose
Initialize the PostgreSQL, Redis, Celery, and FastAPI application containers:
```bash
docker-compose up -d
```

### 2. Set Up Python Environment
Create a virtual environment and install the required dependencies:
```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Apply Database Migrations
Alembic is the authoritative schema-management path:
```bash
alembic -c backend/alembic.ini upgrade head
```

To populate a new database with labeled demo data, run:

```bash
PYTHONPATH=. python -m backend.app.core.seed_db
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

Operational probes are available at `/health/live` and `/health/ready`. The
readiness probe verifies PostgreSQL, Redis, and an active Celery worker. Set
`CORS_ALLOWED_ORIGINS` to a comma-separated list of trusted frontend origins.

Evaluation history endpoints are paginated. Granular results are retrieved
with `GET /api/v1/evaluations/{run_id}/results?skip=0&limit=100`; run summaries
do not load every result row.

---

## Performance & Cost Metrics

The following metrics represent baseline results collected during local benchmark runs:

* **Average Query Latency:** 450ms - 505ms per API response.
* **Average Instance Query Cost:** $0.00036 USD per query.
* **Accuracy Score Range:** 4.0 - 4.5 out of 5.0 (graded by Claude-as-a-Judge).
* **Measured Hallucination Rate:** 0.0% under standard reasoning test suites.
