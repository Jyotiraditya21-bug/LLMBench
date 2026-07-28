import asyncio
from typing import List, Optional

from celery.signals import worker_process_init
from sqlalchemy import delete
from sqlalchemy.future import select

from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.core.database import async_session_maker, engine
from backend.app.models.dataset import TestCase
from backend.app.models.evaluation import EvaluationResult, EvaluationRun
from backend.app.models.prompt import Prompt
from backend.app.schemas.evaluation import SUPPORTED_MODELS
from backend.app.workers.evaluator import (
    ProviderConfigurationError,
    call_target_llm,
    evaluate_with_judge,
)


TERMINAL_STATUSES = {"COMPLETED", "DEMO_COMPLETED", "FAILED", "CANCELLED"}


class PermanentEvaluationError(RuntimeError):
    """A task failure that retrying cannot correct."""


@worker_process_init.connect
def init_worker(**kwargs):
    """Dispose inherited connections so each worker creates its own pool."""
    try:
        engine.sync_engine.dispose()
    except Exception:
        pass


async def _set_task_state(
    run_id: int,
    *,
    status: str,
    error: Optional[BaseException] = None,
    attempt: Optional[int] = None,
) -> None:
    async with async_session_maker() as db:
        run = await db.get(EvaluationRun, run_id)
        if not run or run.status in {"COMPLETED", "DEMO_COMPLETED", "CANCELLED"}:
            return
        metrics = dict(run.metrics or {})
        if error is not None:
            metrics["error"] = str(error)[:1_000]
            metrics["error_type"] = type(error).__name__
        if attempt is not None:
            metrics["attempt"] = attempt
        run.status = status
        run.metrics = metrics
        await db.commit()


@celery_app.task(
    bind=True,
    name="backend.app.workers.tasks.run_evaluation_task",
    max_retries=settings.EVALUATION_TASK_MAX_RETRIES,
    soft_time_limit=settings.EVALUATION_TASK_SOFT_LIMIT_SECONDS,
    time_limit=settings.EVALUATION_TASK_HARD_LIMIT_SECONDS,
    acks_late=True,
    reject_on_worker_lost=True,
)
def run_evaluation_task(self, run_id: int, models: List[str]) -> str:
    """Execute an evaluation with bounded retries and a hard time limit."""
    attempt = self.request.retries + 1
    task_id = self.request.id
    delivery_info = self.request.delivery_info or {}
    redelivered = bool(delivery_info.get("redelivered"))
    try:
        return asyncio.run(
            async_run_evaluation(
                run_id,
                models,
                task_id=task_id,
                attempt=attempt,
                resume_interrupted=redelivered,
            )
        )
    except (PermanentEvaluationError, ProviderConfigurationError) as exc:
        asyncio.run(
            _set_task_state(run_id, status="FAILED", error=exc, attempt=attempt)
        )
        raise
    except Exception as exc:
        if self.request.retries < self.max_retries:
            asyncio.run(
                _set_task_state(run_id, status="RETRYING", error=exc, attempt=attempt)
            )
            raise self.retry(
                exc=exc,
                countdown=min(5 * (2 ** self.request.retries), 60),
            )
        asyncio.run(
            _set_task_state(run_id, status="FAILED", error=exc, attempt=attempt)
        )
        raise


async def async_run_evaluation(
    run_id: int,
    models: List[str],
    *,
    task_id: Optional[str] = None,
    attempt: int = 1,
    resume_interrupted: bool = False,
) -> str:
    """Run one idempotent evaluation attempt and persist incremental progress."""
    invalid_models = sorted(set(models) - set(SUPPORTED_MODELS))
    if not models or invalid_models:
        raise PermanentEvaluationError(
            f"Invalid model selection: {invalid_models or 'no models selected'}"
        )
    if len(models) != len(set(models)):
        raise PermanentEvaluationError("Model selection contains duplicates")

    async with async_session_maker() as db:
        run = await db.get(EvaluationRun, run_id)
        if not run:
            raise PermanentEvaluationError(f"Evaluation run {run_id} not found")
        if run.status in TERMINAL_STATUSES:
            return f"Run {run_id} already reached terminal state {run.status}."
        if run.status == "RUNNING" and not resume_interrupted:
            return f"Run {run_id} is already running; duplicate delivery ignored."

        test_case_result = await db.execute(
            select(TestCase).filter(TestCase.dataset_id == run.dataset_id)
        )
        test_cases = test_case_result.scalars().all()
        if not test_cases:
            raise PermanentEvaluationError("Dataset contains zero test cases")

        prompt_obj = await db.get(Prompt, run.prompt_id) if run.prompt_id else None
        total_expected = len(test_cases) * len(models)

        # A retry starts from a clean slate. The database uniqueness constraint is
        # the final guard against duplicate results from repeated deliveries.
        await db.execute(
            delete(EvaluationResult).where(
                EvaluationResult.evaluation_run_id == run.id
            )
        )
        metrics = dict(run.metrics or {})
        metrics.update(
            {
                "task_id": task_id or metrics.get("task_id"),
                "models": models,
                "attempt": attempt,
                "progress": {"completed": 0, "total": total_expected},
            }
        )
        run.status = "RUNNING"
        run.metrics = metrics
        await db.commit()

        total_cost = 0.0
        total_latency = 0.0
        sum_accuracy = 0.0
        sum_completeness = 0.0
        sum_hallucination = 0.0
        sum_tone = 0.0
        sum_reasoning = 0.0
        hallucinated_count = 0
        results_count = 0
        used_demo_data = False

        for test_case in test_cases:
            for model in models:
                await db.refresh(run)
                if run.status == "CANCELLED":
                    return f"Run {run_id} was cancelled after {results_count} results."

                system_prompt = prompt_obj.system_prompt if prompt_obj else None
                user_prompt = (
                    prompt_obj.user_template.replace(
                        "{{question}}", test_case.question
                    )
                    if prompt_obj
                    else test_case.question
                )

                target_response = await asyncio.wait_for(
                    call_target_llm(
                        model=model,
                        system_prompt=system_prompt,
                        prompt_text=user_prompt,
                    ),
                    timeout=settings.MODEL_CALL_TIMEOUT_SECONDS,
                )
                judge_response = await asyncio.wait_for(
                    evaluate_with_judge(
                        question=test_case.question,
                        ground_truth=test_case.ground_truth,
                        model_output=target_response["output"],
                    ),
                    timeout=settings.MODEL_CALL_TIMEOUT_SECONDS,
                )

                await db.refresh(run)
                if run.status == "CANCELLED":
                    return f"Run {run_id} was cancelled after {results_count} results."

                used_demo_data = (
                    used_demo_data
                    or target_response.get("is_mock", False)
                    or judge_response.get("is_mock", False)
                )
                total_cost += target_response["cost"]
                total_latency += target_response["latency_ms"]
                sum_accuracy += judge_response["accuracy"]
                sum_completeness += judge_response["completeness"]
                sum_hallucination += judge_response["hallucination"]
                sum_tone += judge_response["tone"]
                sum_reasoning += judge_response["reasoning"]
                if judge_response["hallucination"] <= 3.0:
                    hallucinated_count += 1
                results_count += 1

                db.add(
                    EvaluationResult(
                        evaluation_run_id=run.id,
                        test_case_id=test_case.id,
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
                )
                metrics = dict(run.metrics or {})
                metrics["progress"] = {
                    "completed": results_count,
                    "total": total_expected,
                }
                run.metrics = metrics
                await db.commit()

        await db.refresh(run)
        if run.status == "CANCELLED":
            return f"Run {run_id} was cancelled after {results_count} results."

        run.metrics = {
            **dict(run.metrics or {}),
            "total_results": results_count,
            "total_cost": round(total_cost, 6),
            "average_latency_ms": round(total_latency / results_count, 2),
            "average_accuracy": round(sum_accuracy / results_count, 2),
            "average_completeness": round(sum_completeness / results_count, 2),
            "average_hallucination": round(sum_hallucination / results_count, 2),
            "average_tone": round(sum_tone / results_count, 2),
            "average_reasoning": round(sum_reasoning / results_count, 2),
            "hallucination_rate": round(
                hallucinated_count / results_count, 4
            ),
            "evaluation_mode": "DEMO" if used_demo_data else "REAL",
            "contains_mock_data": used_demo_data,
            "progress": {"completed": results_count, "total": total_expected},
        }
        run.status = "DEMO_COMPLETED" if used_demo_data else "COMPLETED"
        await db.commit()
        return (
            f"Run {run_id} completed successfully. "
            f"Evaluated {results_count} instances."
        )
