# EvalForge: LLM Evaluation & Regression Testing Platform

EvalForge is a production-grade AI Quality Engineering platform designed to run LLM evaluations, prompt comparisons, cost optimizations, security red-teaming, and agent-driven failure analysis.

Think of it as: **"PyTest + GitHub Actions + Datadog, but for LLMs."**

---

## 🌟 Core Features

1. **Dataset Management:** Version control, categorizations (factual QA, safety, RAG, tone, hallucination), and JSON imports.
2. **Multi-Model Evaluator:** Concurrent performance testing of prompts against Claude, GPT-4o, Gemini, and Open Source models.
3. **LLM-as-a-Judge:** Automated strict JSON evaluations via Claude checking five key dimensions (Accuracy, Completeness, Hallucination, Tone, Reasoning).
4. **Prompt Arena:** A/B versioning testing and leaderboards highlighting quality-to-cost ratios.
5. **Regression Quality Gates:** System degradation alarms comparing cost, latency, error rate, and hallucination scores.
6. **Root Cause Analysis (RCA) Agent:** LLM synthesizer analyzing failed evaluations to pinpoint errors and recommend prompt corrections.
7. **AI Red Team Agent:** Automated generation of adversarial test cases (jailbreaks, prompt injection, and semantic traps).
8. **Cost Optimizer:** Metric dashboard plotting efficiency frontiers of different models.
9. **CI/CD Integrations:** Automated quality gates simulating pull request check blocks.

---

## 📁 Repository Structure

Refer to [phase_01_architecture.md](file:///Users/jimmycodes/LLMBench/progress/phase_01_architecture.md) for full folder and system design breakdowns.

```
project-root/
├── backend/            # FastAPI, Pydantic, Celery, and Alembic database engine
├── frontend/           # Streamlit Web App dashboard and Plotly graphs
├── agents/             # Root Cause and Red Team LLM reasoning pipelines
├── docs/               # Technical designs and APIs documentation
├── tests/              # Pytest suites (unit, integration, and mocks)
├── progress/           # Step-by-step development phase tracking
├── agent.md            # Agent tracking dashboard
└── docker-compose.yml  # Docker environment configurations
```

---

## 🛠️ Getting Started

For full system architectures, setups, and development logs, see:
- [Agent Tracking Dashboard](file:///Users/jimmycodes/LLMBench/agent.md)
- [Phase 1: Architecture Blueprint](file:///Users/jimmycodes/LLMBench/progress/phase_01_architecture.md)
