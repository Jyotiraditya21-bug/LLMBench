import json
import re
import time
from typing import Any, Dict, Optional

# AI SDK clients
import anthropic
import google.generativeai as genai
import openai

from backend.app.core.config import settings

# --- Pricing Configurations (Cost per 1M tokens) ---
MODEL_PRICING = {
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
}


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculates LLM query costs based on input and output tokens count."""
    pricing = MODEL_PRICING.get(model_name.lower())
    if not pricing:
        # Default to gpt-4o pricing for unlisted models
        pricing = MODEL_PRICING["gpt-4o"]
    
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


async def call_target_llm(
    model: str, system_prompt: Optional[str], prompt_text: str
) -> Dict[str, Any]:
    """Invokes target LLM model under evaluation.

    Returns output content, token counts, processing cost, and latency timer.
    """
    start_time = time.perf_counter()
    output = ""
    prompt_tokens = 0
    completion_tokens = 0

    # Ensure lowercase model identifier
    model_lower = model.lower()

    # --- Case 1: OpenAI Models ---
    if model_lower.startswith("gpt-"):
        if not settings.OPENAI_API_KEY:
            # Fallback mock response for sandbox safety
            time.sleep(0.5)
            output = f"[MOCK OPENAI {model}] Answer to: '{prompt_text[:40]}...'"
            prompt_tokens = len(prompt_text) // 4
            completion_tokens = len(output) // 4
        else:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt_text})
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
            )
            output = response.choices[0].message.content or ""
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0

    # --- Case 2: Anthropic Models ---
    elif model_lower.startswith("claude-"):
        if not settings.ANTHROPIC_API_KEY:
            time.sleep(0.6)
            output = f"[MOCK ANTHROPIC {model}] Answer to: '{prompt_text[:40]}...'"
            prompt_tokens = len(prompt_text) // 4
            completion_tokens = len(output) // 4
        else:
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            system_param = system_prompt if system_prompt else anthropic.NotGiven()
            
            response = await client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_param,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.2,
            )
            output = "".join([block.text for block in response.content if hasattr(block, 'text')])
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens

    # --- Case 3: Google Gemini Models ---
    elif model_lower.startswith("gemini-"):
        if not settings.GEMINI_API_KEY:
            time.sleep(0.4)
            output = f"[MOCK GEMINI {model}] Answer to: '{prompt_text[:40]}...'"
            prompt_tokens = len(prompt_text) // 4
            completion_tokens = len(output) // 4
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            gemini_model_name = "gemini-1.5-flash" if "flash" in model_lower else "gemini-1.5-pro"
            client = genai.GenerativeModel(
                model_name=gemini_model_name,
                system_instruction=system_prompt,
            )
            response = await client.generate_content_async(
                prompt_text,
                generation_config={"temperature": 0.2},
            )
            output = response.text
            # Estimate tokens as SDK does not supply it directly in generate_content result
            prompt_tokens = len(prompt_text) // 4
            completion_tokens = len(output) // 4

    # --- Case 4: Default Fallback (Mock) ---
    else:
        time.sleep(0.3)
        output = f"[MOCK {model}] Response for: '{prompt_text[:40]}...'"
        prompt_tokens = len(prompt_text) // 4
        completion_tokens = len(output) // 4

    latency_ms = (time.perf_counter() - start_time) * 1000
    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    return {
        "output": output,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost": cost,
        "latency_ms": latency_ms,
    }


# --- Claude-As-A-Judge Loop ---

JUDGE_PROMPT_TEMPLATE = """You are an objective AI Quality Evaluation Judge.
Your task is to grade a target LLM output against the provided ground truth answer.

Analyze the interaction using these 5 dimensions:
1. Accuracy: Does it state facts that align with the ground truth? (1-5)
2. Completeness: Does it answer all parts of the question mentioned in the ground truth? (1-5)
3. Hallucination: Are there unverified or fabricated claims not supported by the ground truth? (1 = heavy hallucination, 5 = no hallucination at all)
4. Tone: Is the tone helpful, professional, and clear? (1-5)
5. Reasoning: Does the thinking or logical deduction follow a sound path? (1-5)

INPUT DATA:
- Question: {question}
- Ground Truth: {ground_truth}
- Model Output: {model_output}

You must return a STRICT JSON object only. Do not wrap it in markdown codeblocks. Do not add intro or outro text.
JSON Structure:
{{
  "accuracy": 5,
  "completeness": 4,
  "hallucination": 5,
  "tone": 5,
  "reasoning": 4,
  "reason": "Detail explanation explaining the scores."
}}
"""


async def evaluate_with_judge(
    question: str, ground_truth: str, model_output: str
) -> Dict[str, Any]:
    """Invokes Anthropic Claude as an evaluation judge.

    Extracts scores for Accuracy, Completeness, Hallucination, Tone, and Reasoning.
    """
    judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        ground_truth=ground_truth,
        model_output=model_output,
    )

    default_result = {
        "accuracy": 4.0,
        "completeness": 4.0,
        "hallucination": 5.0,
        "tone": 4.5,
        "reasoning": 4.0,
        "reason": "Evaluation generated via local mock judge loop.",
    }

    # Choose available API key for the Judge
    raw_text = None
    if settings.ANTHROPIC_API_KEY:
        try:
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = await client.messages.create(
                model="claude-3-haiku-20240307",  # Haiku is fast and cost-effective as a judge
                max_tokens=800,
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.0,  # Zero temperature for deterministic evaluations
            )
            raw_text = "".join([block.text for block in response.content if hasattr(block, 'text')]).strip()
        except Exception:
            pass

    if not raw_text and settings.OPENAI_API_KEY:
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": judge_prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            raw_text = response.choices[0].message.content or ""
        except Exception:
            pass

    if not raw_text and settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            client = genai.GenerativeModel("gemini-1.5-flash")
            response = await client.generate_content_async(
                judge_prompt,
                generation_config={"temperature": 0.0, "response_mime_type": "application/json"}
            )
            raw_text = response.text
        except Exception:
            pass

    if not raw_text:
        # Fallback mock judge evaluation if no APIs worked or are configured
        time.sleep(0.5)
        if len(model_output) < len(ground_truth) // 2:
            default_result["completeness"] = 2.0
            default_result["reason"] = "Mock Judge: Answer appears significantly shorter than expected ground truth."
        return default_result

    try:
        # Clean JSON markdown blocks if any returned
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

        parsed_json = json.loads(raw_text)
        
        # Verify required keys exist
        required_keys = ["accuracy", "completeness", "hallucination", "tone", "reasoning", "reason"]
        for key in required_keys:
            if key not in parsed_json:
                parsed_json[key] = default_result[key]
                
        return parsed_json

    except Exception as e:
        # Graceful degradation on JSON parsing or API faults
        default_result["reason"] = f"Failed to parse Judge output. Error: {str(e)}"
        return default_result
