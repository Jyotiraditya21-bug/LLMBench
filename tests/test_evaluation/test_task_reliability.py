import pytest
from pydantic import ValidationError

from backend.app.schemas.evaluation import EvaluationResultCreate
from backend.app.workers.tasks import (
    PermanentEvaluationError,
    async_run_evaluation,
    run_evaluation_task,
)


def test_task_has_bounded_retries_and_time_limits() -> None:
    assert run_evaluation_task.max_retries == 2
    assert run_evaluation_task.soft_time_limit == 1_800
    assert run_evaluation_task.time_limit == 1_860
    assert run_evaluation_task.acks_late is True
    assert run_evaluation_task.reject_on_worker_lost is True


@pytest.mark.asyncio
async def test_worker_revalidates_models_before_database_work() -> None:
    with pytest.raises(PermanentEvaluationError, match="Invalid model selection"):
        await async_run_evaluation(1, ["untrusted-model"])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("accuracy", 6),
        ("prompt_tokens", -1),
        ("cost", float("inf")),
        ("latency_ms", -0.1),
    ],
)
def test_evaluation_result_rejects_invalid_numeric_values(
    field: str,
    value: float,
) -> None:
    payload = {
        "evaluation_run_id": 1,
        "test_case_id": 1,
        "model_name": "gpt-4o",
        "raw_output": "answer",
        field: value,
    }

    with pytest.raises(ValidationError):
        EvaluationResultCreate.model_validate(payload)
