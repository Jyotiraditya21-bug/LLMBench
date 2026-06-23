# Phase 8: Dockerization & CI/CD Simulated Quality Gate

This document records the Docker orchestration layouts and the GitHub Actions CI/CD Quality Gate pipelines built during Phase 8.

---

## 1. Summary of Files Created

1. **[backend/Dockerfile](file:///Users/jimmycodes/LLMBench/backend/Dockerfile):** Packages the FastAPI application, sets the python path configuration, and exposes port 8000.
2. **[frontend/Dockerfile](file:///Users/jimmycodes/LLMBench/frontend/Dockerfile):** Packages the Streamlit application and exposes port 8501.
3. **[docker-compose.yml](file:///Users/jimmycodes/LLMBench/docker-compose.yml):** Builds and runs the Postgres, Redis, FastAPI, Celery Worker, and Streamlit services as a unified network stack.
4. **[backend/app/workers/quality_gate.py](file:///Users/jimmycodes/LLMBench/backend/app/workers/quality_gate.py):** Automation script that runs evaluations, polls for status, calls the comparison endpoint, and exits with error code 1 on score degradation.
5. **[.github/workflows/ai_quality_gate.yml](file:///Users/jimmycodes/LLMBench/.github/workflows/ai_quality_gate.yml):** GitHub Actions workflow executing the Quality Gate validation suite on PR submissions.

---

## 2. Core Code Section Explanations

### CI Quality Gate Failure Decision (`sys.exit(1)`)
```python
if score_delta <= ACCURACY_DROP_THRESHOLD:
    print(f"\n❌ QUALITY GATE FAILED: Score degradation ({score_delta:+.2f}) exceeds the limit.")
    sys.exit(1)
else:
    print(f"\n✅ QUALITY GATE PASSED.")
    sys.exit(0)
```
- **Like I am 5 years old 🧸:** Before letting the builders add new toys to the shelf, we run a test. If the new toy is worse than the old toy (scores drop too much), we wave a red flag (`sys.exit(1)`) and stop the conveyor belt from moving!
- **Industry Relevance 🚀:** Conventional CI/CD compiles code and runs unit tests, but misses LLM quality regressions. A custom script that executes a test suite and returns non-zero codes on quality degradation acts as a "Quality Gate," preventing developers from shipping prompts that lower production accuracy.
- **Interview Relevance 🎤:** *How do you implement an AI Quality Gate in a CI/CD pipeline?* We build a script that runs on PR merges. The script triggers a background evaluation run of the new prompts against a test dataset via the backend, polls for completion, and hits the regression compare endpoint. If the accuracy delta falls below our threshold, the script calls `sys.exit(1)`, which instructs the GitHub Actions runner to mark the step as failed and block the PR.

---

### Docker Compose Multi-Container Orchestration
```yaml
services:
  web:
    build: ./backend
    ...
  celery_worker:
    build: ./backend
    ...
    command: celery -A backend.app.core.celery_app worker --loglevel=info
```
- **Like I am 5 years old 🧸:** Instead of loading all the helpers in one small room where they step on each other, we put the manager in one room, the database storage in another, and the backroom workers in another, connecting them with phones (virtual network) so they can work in parallel.
- **Industry Relevance 🚀:** Sharing a single container for a database, worker queue, and API server is a severe anti-pattern. Decoupling them allows scaling worker nodes independently based on prompt benchmark queue length without adding server overhead.
- **Interview Relevance 🎤:** *How do the FastAPI backend and Celery workers interact in your Docker Compose file?* They build from the same backend image context to ensure code synchrony. They share the same environment parameters and connect via a virtual network. The FastAPI backend sends tasks to the Redis container broker, which is monitored by the Celery worker container.
