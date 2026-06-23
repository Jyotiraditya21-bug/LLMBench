# Agent Development Hub — EvalForge

This document maps out the operational personas, project rules, and overall development milestones for building **EvalForge**.

---

## Agent Personas & Roles

To ensure a clean separation of concerns, the project is designed by adopting seven specialized engineering personas:

| Agent Role | Responsibility | Core Scope |
| :--- | :--- | :--- |
| **Architect Agent** | System Design, folder structure, database schema models, and technical standards. | Overall architecture & blueprint |
| **Backend Agent** | FastAPI app development, database connections, migrations (Alembic), REST endpoints, and Celery setup. | API layer & backend tasks |
| **Evaluation Agent** | Implementation of LLM-as-a-Judge, model integrations (Anthropic, OpenAI, Gemini), pricing models, and grading logic. | LLM scoring loop |
| **Red Team Agent** | Automated adversarial test-case generation, prompt injections, boundary-value queries. | Security & Robustness |
| **Frontend Agent** | Visualizing metrics, prompt arena comparison, cost analysis dashboards in Streamlit. | UI & charts (Streamlit / Plotly) |
| **Testing Agent** | Formulating Pytest suites, mocks, integration testing, and simulation runs. | Quality Assurance |
| **DevOps Agent** | Docker Compose orchestration, Redis configuration, and CI/CD quality gate setup. | Infrastructure & Pipeline |

---

## Technical Standards

We adhere strictly to:
1. **Clean Architecture:** Domain and storage layers remain completely decoupled. Datasets, evaluations, and metrics utilize clear schemas.
2. **SOLID Principles:** Single Responsibility is applied down to individual router modules and LLM connectors.
3. **Repository Pattern:** CRUD transactions are encapsulated away from REST endpoints to allow easy mocking and database swapping.
4. **Asynchronous APIs:** FastAPI routing leverages fully asynchronous paths (`async def` with `asyncio`).
5. **Robust Validation:** Pydantic v2 schemas control inputs and outputs, enforcing strict validation boundaries.
6. **Detailed Explanations:** Every file, script, and database model must be explained thoroughly, catering to both architectural design principles and interview contexts.

---

## Development Roadmap

- [x] **Phase 1: Architecture & Project Directory Setup**
- [x] **Phase 2: Database Schema & Migration Configurations**
- [x] **Phase 3: Dataset, Prompt, & REST Router Implementations**
- [x] **Phase 4: LLM Judge Loop & Background Task Workers (Celery)**
- [x] **Phase 5: Streamlit Frontend Dashboard**
- [x] **Phase 6: RCA Agent & AI Red Team Agent Integration**
- [x] **Phase 7: Testing suites (Unit & Integration Mocks)**
- [x] **Phase 8: Dockerization & CI/CD Simulated Quality Gate**
