# Phase 4: Async Evaluation & LLM Judge System

This document captures the implementation details of the background Celery orchestration and the LLM-as-a-Judge evaluation logic.

---

## 1. Summary of Files Created

1. **[core/celery_app.py](file:///Users/jimmycodes/LLMBench/backend/app/core/celery_app.py):** Initializes the Celery background worker connected to Redis, optimization parameters, and sets the task prefetch limits.
2. **[workers/evaluator.py](file:///Users/jimmycodes/LLMBench/backend/app/workers/evaluator.py):** SDK clients wrappers for OpenAI, Anthropic, and Gemini. Calculates costs dynamically and defines the prompt structure for the Claude-as-a-Judge evaluation.
3. **[workers/tasks.py](file:///Users/jimmycodes/LLMBench/backend/app/workers/tasks.py):** Celery background tasks running the async evaluation loop, mapping prompt variables, updating database statuses, and collecting aggregated metrics.

---

## 2. Core Code Section Explanations

### Claude LLM-as-a-Judge Prompt Design
We prompt Claude to score on five separate dimensions: Accuracy, Completeness, Hallucination, Tone, and Reasoning.
```python
JUDGE_PROMPT_TEMPLATE = """...
Analyze the interaction using these 5 dimensions:
1. Accuracy: Does it state facts that align with the ground truth? (1-5)
2. Completeness: Does it answer all parts of the question mentioned in the ground truth? (1-5)
3. Hallucination: Are there unverified or fabricated claims not supported by the ground truth? (1 = heavy hallucination, 5 = no hallucination at all)
4. Tone: Is the tone helpful, professional, and clear? (1-5)
5. Reasoning: Does the thinking or logical deduction follow a sound path? (1-5)
...
"""
```
- **Like I am 5 years old 🧸:** When the teacher grades your homework, she doesn't just draw a happy face. She checks: Did you write the correct answers? Did you answer all of them? Did you make up stories? Were you polite? Did you explain your work? That is exactly what this Claude judge prompt does!
- **Industry Relevance 🚀:** Relying on simple string distance metrics (like ROUGE or BLEU) doesn't capture semantic correctness. Semantic grading via a high-performing LLM-as-a-Judge yields a 90%+ correlation with human evaluation.
- **Interview Relevance 🎤:** *How do you prompt an LLM to evaluate another LLM's output?* By specifying structured dimensions, scoring scales (1-5), providing the question, model output, and ground truth in separate fields, and forcing a strict JSON output shape containing both numeric grades and reasoning text.

---

### Mixing Celery Task Threads with Async Loops (`asyncio.run`)
```python
@celery_app.task
def run_evaluation_task(run_id: int, models: List[str]):
    try:
        return asyncio.run(async_run_evaluation(run_id, models))
    ...
```
- **Like I am 5 years old 🧸:** Celery is like a truck driver who can only do one task at a time and doesn't understand "waiting in line". We give him a magic engine (`asyncio.run`) that lets him carry multiple phone calls at once inside the truck without getting confused.
- **Industry Relevance 🚀:** Celery task workers run in synchronous worker loops, but calling multiple external LLM APIs concurrently is best done using async/await syntax. `asyncio.run()` links these paradigms, allowing workers to execute async database and networking tasks cleanly.
- **Interview Relevance 🎤:** *How do you execute asynchronous database and API calls inside a synchronous Celery task?* By invoking an `asyncio.run` wrapper inside the Celery task function. This starts an event loop for the duration of the task, enabling clean `async/await` syntax for database connection contexts and HTTP client calls.
