# Phase 6: Root Cause & Red Team Agents

This document logs the development, prompt designs, and integration patterns of the Root Cause Analysis (RCA) and AI Red Team agents built during Phase 6.

---

## 1. Summary of Files Created / Modified

1. **[agents/rca_agent.py](file:///Users/jimmycodes/LLMBench/agents/rca_agent.py):** Implements failure analytics logic by fetching runs scoring low accuracy (<=3) and prompting Claude to compile common failure patterns and recommended prompt scaffolding remedies.
2. **[agents/red_team_agent.py](file:///Users/jimmycodes/LLMBench/agents/red_team_agent.py):** Implements security auditing logic, taking seed QA test cases and generating misleading variations, outdated traps, ambiguous queries, and prompt injections.
3. **[backend/app/api/v1/agents.py](file:///Users/jimmycodes/LLMBench/backend/app/api/v1/agents.py):** API endpoints exposing the agents. Automatically clones datasets and saves newly generated adversarial test cases directly to the database.
4. **[backend/app/api/v1/router.py](file:///Users/jimmycodes/LLMBench/backend/app/api/v1/router.py) (Modified):** Registered the agents router under the `/agents` namespace.
5. **[frontend/pages/04_rca_console.py](file:///Users/jimmycodes/LLMBench/frontend/pages/04_rca_console.py):** Interactive interface triggering failure reports and red-team runs, showing attacks in real-time.
6. **[frontend/pages/05_cost_analytics.py](file:///Users/jimmycodes/LLMBench/frontend/pages/05_cost_analytics.py):** Analysis panel mapping model spending, latencies, and outputting efficiency savings recommendations.

---

## 2. Core Code Section Explanations

### Automated Cloning & Bulk Insertion of Adversarial Datasets
```python
adv_name = f"{dataset.name} [RedTeam-Adversarial]"
# Create Dataset object
adv_dataset = Dataset(name=adv_name, ...)
db.add(adv_dataset)
...
for ac in adversarial_cases:
    tc_obj = TestCase(dataset_id=adv_dataset.id, ...)
    db.add(tc_obj)
await db.commit()
```
- **Like I am 5 years old 🧸:** When the Red Team elf makes up tricky trick questions, we don't make you write them down yourself. We automatically open a new, shiny scrapbook labeled "Trick Questions Folder," write all the trick questions down, and put it on your shelf so you can test the robot with them right away!
- **Industry Relevance 🚀:** Generative red teaming is useless if the results are only dumped in a console log. Storing generated adversarial data automatically in the application database allows immediate reuse in regression pipelines.
- **Interview Relevance 🎤:** *How does your application handle AI-assisted test data generation?* The client triggers adversarial generation via the `/agents/redteam` endpoint. The backend queries seed test cases, runs them through our red-team generator, and then automatically saves them as a new, tagged database dataset. This dataset can then be evaluated against prompt configurations instantly.

---

### Failure Synthesis Prompt Design
```python
RCA_SYSTEM_PROMPT = """You are a Principal AI Quality Assurance Engineer and Root Cause Analysis Agent.
Your task is to analyze a list of failed LLM evaluations (low accuracy or poor reasoning) and generate a structured root-cause report in markdown.
...
"""
```
- **Like I am 5 years old 🧸:** Instead of reading each failed test paper separately, the smart agent gathers all the papers with red marks, looks at them all at once, and says: "Ah! The student keeps getting confused when we ask about fractions. Here is how we can explain it better."
- **Industry Relevance 🚀:** Manual debugging of 100+ failed model runs is a massive bottleneck. The RCA Agent automates error synthesis, saving hours of prompt engineering and developer time.
- **Interview Relevance 🎤:** *Explain the concept of an AI Root Cause Agent.* The RCA Agent is an LLM agent programmed with QA personas. By feeding it the input questions, expected answers, actual outputs, and judge's criticisms of failing cases, it performs high-level synthesis to identify systemic prompt deficiencies and suggest fixes.
