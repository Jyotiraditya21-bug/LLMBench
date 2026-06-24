import os
from typing import Any, Dict, List
import anthropic
import google.generativeai as genai
import openai

from backend.app.core.config import settings

RCA_SYSTEM_PROMPT = """You are a Principal AI Quality Assurance Engineer and Root Cause Analysis Agent.
Your task is to analyze a list of failed LLM evaluations (low accuracy or poor reasoning) and generate a structured root-cause report in markdown.

Your report MUST include:
1. Common Failure Patterns (e.g., model gets confused by double negatives, truncates lists, hallucinating figures).
2. Categories or domains most impacted (e.g., medical, coding, logical math).
3. Root Causes (why did the model fail?).
4. Recommended Fixes (such as prompt scaffolding, restoring context from successful runs, or adding few-shot examples).

Provide clear, actionable, developer-centric feedback.
"""

RCA_USER_TEMPLATE = """Here is the list of failed test cases:
{failures_str}

Please synthesize this data and produce your Root Cause Analysis report in Markdown format.
"""


async def analyze_run_failures(failures: List[Dict[str, Any]]) -> str:
    """Analyzes a set of failed evaluation results and synthesizes failure root causes."""
    if not failures:
        return "### Root Cause Analysis\nNo failures detected in this evaluation run! Accuracy is 100%."

    # Format failures for prompt context
    failures_str = ""
    for idx, f in enumerate(failures[:15]):  # Limit to first 15 failures to avoid context bloat
        failures_str += f"""---
[Failure {idx+1}]
Question: {f.get('question')}
Ground Truth: {f.get('ground_truth')}
Model Output: {f.get('output')}
Judge Reason: {f.get('reason')}
"""

    default_report = """### [RCA] Root Cause Analysis Report

#### 1. Common Failure Patterns
* **Context Truncation:** Model output is incomplete compared to the comprehensive ground truth.
* **Negative Prompt Ambiguity:** The model struggled to adhere to the negative constraints (e.g., "do not mention X").

#### 2. Categories Impacted
* **Reasoning / Logic:** 60% degradation in multi-step problem solving.
* **Factual Precision:** 40% failure rate in numerical dates.

#### 3. Identified Root Causes
* The prompt template does not instruct the model to work step-by-step (Chain of Thought), leading to premature concluding remarks.
* The model lacks system context bounding instructions, causing tone variance.

#### 4. Recommended Fixes
* **Implement CoT Scaffold:** Insert: *"Let's think step by step before providing the final answer"* in the system prompt.
* **Few-shot Injection:** Embed 2 representative factual samples into the user template.
"""

    # 1. Attempt Anthropic (Claude 3.5 Sonnet)
    if settings.ANTHROPIC_API_KEY and settings.HAS_ANTHROPIC:
        try:
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = await client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1500,
                system=RCA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": RCA_USER_TEMPLATE.format(failures_str=failures_str)}],
                temperature=0.2,
            )
            return "".join([block.text for block in response.content if hasattr(block, 'text')])
        except Exception:
            pass

    # 2. Attempt OpenAI (GPT-4o)
    if settings.OPENAI_API_KEY:
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": RCA_SYSTEM_PROMPT},
                    {"role": "user", "content": RCA_USER_TEMPLATE.format(failures_str=failures_str)}
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            return response.choices[0].message.content or ""
        except Exception:
            pass

    # 3. Attempt Gemini (Gemini 1.5 Pro)
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            client = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                system_instruction=RCA_SYSTEM_PROMPT
            )
            response = await client.generate_content_async(
                RCA_USER_TEMPLATE.format(failures_str=failures_str),
                generation_config={"temperature": 0.2, "max_output_tokens": 1500}
            )
            return response.text
        except Exception:
            pass

    # 4. Fallback mock report
    return "*(MOCK AGENT)*\n\n" + default_report
