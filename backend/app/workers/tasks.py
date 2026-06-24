import asyncio
import traceback
from typing import List

from celery.signals import worker_process_init
from backend.app.core.celery_app import celery_app
from backend.app.core.database import async_session_maker, engine
from backend.app.models.dataset import TestCase
from backend.app.models.evaluation import EvaluationResult, EvaluationRun
from backend.app.models.prompt import Prompt
from backend.app.workers.evaluator import call_target_llm, evaluate_with_judge


@worker_process_init.connect
def init_worker(**kwargs):
    """Dispose parent process connection pool upon fork to ensure children establish fresh connections."""
    try:
        engine.sync_engine.dispose()
    except Exception:
        pass


@celery_app.task(name="backend.app.workers.tasks.run_evaluation_task")
def run_evaluation_task(run_id: int, models: List[str]) -> str:
    """Synchronous Celery task wrapper that runs the async evaluation loop."""
    try:
        return asyncio.run(async_run_evaluation(run_id, models))
    except Exception as e:
        # Emergency backup fail-safe
        return f"Celery task execution failed: {str(e)}"


async def async_run_evaluation(run_id: int, models: List[str]) -> str:
    """Asynchronous evaluation runner executing LLM queries and scoring."""
    try:
        async with async_session_maker() as db:
            # 1. Fetch Evaluation Run record
            run = await db.get(EvaluationRun, run_id)
            if not run:
                return f"Error: Evaluation run {run_id} not found."

            try:
                # Update status to RUNNING
                run.status = "RUNNING"
                await db.commit()

                # 2. Fetch dataset test cases
                from sqlalchemy.future import select
                tc_result = await db.execute(
                    select(TestCase).filter(TestCase.dataset_id == run.dataset_id)
                )
                test_cases = tc_result.scalars().all()

                if not test_cases:
                    run.status = "FAILED"
                    run.metrics = {"error": "Dataset contains zero test cases."}
                    await db.commit()
                    return f"Run {run_id} failed: No test cases found."

                # 3. Fetch prompt template if registered
                prompt_obj = None
                if run.prompt_id:
                    prompt_obj = await db.get(Prompt, run.prompt_id)

                total_cost = 0.0
                total_latency = 0.0
                results_count = 0

                # Accumulator fields for scores
                sum_accuracy = 0.0
                sum_completeness = 0.0
                sum_hallucination = 0.0
                sum_tone = 0.0
                sum_reasoning = 0.0
                hallucinated_count = 0

                # 4. Orchestrate evaluation executions
                # We process test cases sequentially to avoid API rate limits, but models in parallel
                for tc in test_cases:
                    for model in models:
                        # Assemble user prompt based on template variables
                        system_prompt = prompt_obj.system_prompt if prompt_obj else None
                        if prompt_obj:
                            # Simple replacement of {{question}} with active test case question
                            user_prompt = prompt_obj.user_template.replace("{{question}}", tc.question)
                        else:
                            user_prompt = tc.question

                        # Invoke target LLM model
                        target_response = await call_target_llm(
                            model=model,
                            system_prompt=system_prompt,
                            prompt_text=user_prompt,
                        )

                        # Evaluate response using Claude-as-a-Judge
                        judge_response = await evaluate_with_judge(
                            question=tc.question,
                            ground_truth=tc.ground_truth,
                            model_output=target_response["output"],
                        )

                        # Record stats
                        total_cost += target_response["cost"]
                        total_latency += target_response["latency_ms"]
                        results_count += 1

                        # Increment score sums
                        sum_accuracy += judge_response["accuracy"]
                        sum_completeness += judge_response["completeness"]
                        sum_hallucination += judge_response["hallucination"]
                        sum_tone += judge_response["tone"]
                        sum_reasoning += judge_response["reasoning"]

                        # Consider it a hallucination if judge scores hallucination <= 3.0 (meaning claims failed ground truth)
                        if judge_response["hallucination"] <= 3.0:
                            hallucinated_count += 1

                        # Write individual Result back to database
                        result_record = EvaluationResult(
                            evaluation_run_id=run.id,
                            test_case_id=tc.id,
                            model_name=model,
                            raw_output=target_response["output"],
                            prompt_tokens=target_response["prompt_tokens"],
                            completion_tokens=target_response["completion_tokens"],
                            cost=target_response["cost"],
                            latency_ms=target_response["latency_ms"],
                            accuracy=judge_response["accuracy"],
                            completeness=judge_response["completeness"],
                            hallucination=judge_response["hallucination"],
                            tone=judge_response["tone"],
                            reasoning=judge_response["reasoning"],
                            reason=judge_response["reason"],
                        )
                        db.add(result_record)

                # 5. Compile aggregate metrics
                if results_count > 0:
                    avg_accuracy = sum_accuracy / results_count
                    avg_completeness = sum_completeness / results_count
                    avg_hallucination = sum_hallucination / results_count
                    avg_tone = sum_tone / results_count
                    avg_reasoning = sum_reasoning / results_count
                    avg_latency = total_latency / results_count
                    hallucination_rate = hallucinated_count / results_count
                else:
                    avg_accuracy = avg_completeness = avg_hallucination = avg_tone = avg_reasoning = avg_latency = hallucination_rate = 0.0

                run.metrics = {
                    "total_results": results_count,
                    "total_cost": round(total_cost, 6),
                    "average_latency_ms": round(avg_latency, 2),
                    "average_accuracy": round(avg_accuracy, 2),
                    "average_completeness": round(avg_completeness, 2),
                    "average_hallucination": round(avg_hallucination, 2),
                    "average_tone": round(avg_tone, 2),
                    "average_reasoning": round(avg_reasoning, 2),
                    "hallucination_rate": round(hallucination_rate, 4),
                }

                run.status = "COMPLETED"
                await db.commit()
                return f"Run {run_id} completed successfully. Evaluated {results_count} instances."

            except Exception as e:
                # Gracefully log faults to Postgres
                await db.rollback()
                run.status = "FAILED"
                run.metrics = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
                await db.commit()
                return f"Run {run_id} failed: {str(e)}"
    finally:
        await engine.dispose()

