# LLMBench: LLM Evaluation and Regression Testing Platform

LLMBench is an AI quality engineering platform designed for LLM evaluation, prompt comparison, regression checking, and cost optimization. It helps engineers benchmark prompts, measure latencies and costs, and detect quality regression between prompt versions using a dynamic Prompt Arena dashboard.

## Tech Stack
* Backend: FastAPI, SQLAlchemy, Pydantic
* Background Worker: Celery, Redis
* Database: PostgreSQL
* Frontend: Vanilla HTML, CSS, JavaScript, Plotly
* Testing: Pytest

## Repository Structure
This repository is configured as a portfolio showcase that highlights the platform's architecture, client-side interface, testing suites, and deployment configuration, while ignoring internal backend execution details.

* backend/app/static/ - Frontend Single Page Application (HTML, CSS, JavaScript)
* tests/ - Automated pytest suites validating dataset and evaluation logic
* docker-compose.yml - Orchestration files for database, queue, and application services
* backend/Dockerfile - Container build specifications

## Setup Steps
To run the platform locally, follow these steps:

1. Clone the repository and navigate to the project folder.
2. Launch the database and queue services:
   ```bash
   docker-compose up -d db redis
   ```
3. Initialize the Python virtual environment and install dependencies:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Start the FastAPI application:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
5. In a separate terminal, launch the Celery background worker:
   ```bash
   celery -A backend.app.core.celery_app worker --pool=solo --loglevel=info
   ```
6. Open your browser and navigate to the local dashboard at http://localhost:8000/.

To run the automated test suite, execute:
```bash
PYTHONPATH=. backend/.venv/bin/pytest
```

## Performance Metrics
The platform records detailed latency, cost, and accuracy dimensions. Based on baseline runs executed against mock LLM APIs:

* Average latency: 450ms - 505ms per query
* Average query cost: $0.00036 per instance ($0.00072 total cost for 2 instances)
* Accuracy Score range: 4.0 - 4.5 out of 5.0 (graded by Claude-as-a-Judge)
* Hallucination Rate: 0.0% (measured using target constraints)
