from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.models.dataset import Dataset, TestCase as CaseModel
from backend.app.models.prompt import Prompt
from backend.app.models.evaluation import EvaluationRun
from backend.app.models.regression import RegressionReport


@pytest.mark.asyncio
async def test_trigger_evaluation_success(client: AsyncClient, mock_db: AsyncMock) -> None:
    """Asserts that triggering evaluation with valid data schedules task and returns HTTP 202."""
    now = datetime.now(timezone.utc)
    mock_dataset = Dataset(
        id=1,
        name="Test DS",
        version="1.0",
        category="general",
        test_cases=[
            CaseModel(
                id=1,
                dataset_id=1,
                question="Question",
                ground_truth="Answer",
                category="general",
                meta_data={},
            )
        ],
    )
    mock_prompt = Prompt(
        id=2,
        name="Test Prompt",
        version="1.0",
        user_template="{{question}}",
    )
    mock_run = EvaluationRun(id=10, dataset_id=1, prompt_id=2, status="PENDING", snapshot={}, created_at=now, updated_at=now)

    with patch("backend.app.api.v1.evaluations.crud_dataset.dataset.get", new_callable=AsyncMock) as mock_get_ds, \
         patch("backend.app.api.v1.evaluations.crud_prompt.prompt.get", new_callable=AsyncMock) as mock_get_pr, \
         patch("backend.app.api.v1.evaluations.crud_eval.evaluation_run.create", new_callable=AsyncMock) as mock_create_run, \
         patch("backend.app.workers.tasks.run_evaluation_task.apply_async") as mock_celery_dispatch:
        
        mock_get_ds.return_value = mock_dataset
        mock_get_pr.return_value = mock_prompt
        mock_create_run.return_value = mock_run
        mock_celery_dispatch.return_value = MagicMock(id="task-123")

        payload = {
            "dataset_id": 1,
            "prompt_id": 2,
            "models": ["gpt-4o"]
        }
        response = await client.post("/api/v1/evaluations/trigger", json=payload)
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["id"] == 10
        mock_celery_dispatch.assert_called_once_with(args=[10, ["gpt-4o"]])
        assert mock_run.metrics["task_id"] == "task-123"


@pytest.mark.asyncio
async def test_trigger_evaluation_dataset_not_found(client: AsyncClient, mock_db: AsyncMock) -> None:
    """Asserts triggering an evaluation with a non-existent dataset ID returns HTTP 404."""
    with patch("backend.app.api.v1.evaluations.crud_dataset.dataset.get", new_callable=AsyncMock) as mock_get_ds:
        mock_get_ds.return_value = None

        payload = {
            "dataset_id": 999,
            "models": ["gpt-4o"]
        }
        response = await client.post("/api/v1/evaluations/trigger", json=payload)
        
        assert response.status_code == 404
        assert "dataset 999 not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_trigger_evaluation_empty_dataset(client: AsyncClient, mock_db: AsyncMock) -> None:
    """Asserts triggering evaluation with an empty dataset (0 test cases) returns HTTP 400."""
    mock_dataset = Dataset(id=1, name="Empty DS", version="1.0", test_cases=[])

    with patch("backend.app.api.v1.evaluations.crud_dataset.dataset.get", new_callable=AsyncMock) as mock_get_ds:
        mock_get_ds.return_value = mock_dataset

        payload = {
            "dataset_id": 1,
            "models": ["gpt-4o"]
        }
        response = await client.post("/api/v1/evaluations/trigger", json=payload)
        
        assert response.status_code == 400
        assert "no test cases" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_trigger_evaluation_prompt_not_found(client: AsyncClient, mock_db: AsyncMock) -> None:
    """Asserts triggering evaluation with a non-existent prompt ID returns HTTP 404."""
    mock_dataset = Dataset(id=1, name="Test DS", version="1.0", test_cases=[AsyncMock()])

    with patch("backend.app.api.v1.evaluations.crud_dataset.dataset.get", new_callable=AsyncMock) as mock_get_ds, \
         patch("backend.app.api.v1.evaluations.crud_prompt.prompt.get", new_callable=AsyncMock) as mock_get_pr:
        
        mock_get_ds.return_value = mock_dataset
        mock_get_pr.return_value = None

        payload = {
            "dataset_id": 1,
            "prompt_id": 888,
            "models": ["gpt-4o"]
        }
        response = await client.post("/api/v1/evaluations/trigger", json=payload)
        
        assert response.status_code == 404
        assert "prompt 888 not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_compare_runs_not_found(client: AsyncClient, mock_db: AsyncMock) -> None:
    """Asserts that comparing runs where one or both do not exist returns HTTP 404."""
    with patch("backend.app.api.v1.evaluations.crud_eval.evaluation_run.get", new_callable=AsyncMock) as mock_get_run:
        mock_get_run.return_value = None

        payload = {
            "baseline_run_id": 100,
            "comparison_run_id": 101
        }
        response = await client.post("/api/v1/evaluations/compare", json=payload)
        
        assert response.status_code == 404
        assert "runs not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_compare_rejects_demo_run(client: AsyncClient, mock_db: AsyncMock) -> None:
    """Demo data must never be accepted as a production regression baseline."""
    now = datetime.now(timezone.utc)
    baseline = EvaluationRun(
        id=1,
        dataset_id=1,
        status="DEMO_COMPLETED",
        metrics={"evaluation_mode": "DEMO"},
        created_at=now,
        updated_at=now,
    )
    comparison = EvaluationRun(
        id=2,
        dataset_id=1,
        status="COMPLETED",
        metrics={"evaluation_mode": "REAL"},
        created_at=now,
        updated_at=now,
    )

    with patch(
        "backend.app.api.v1.evaluations.crud_eval.evaluation_run.get",
        new_callable=AsyncMock,
    ) as mock_get_run:
        mock_get_run.side_effect = [baseline, comparison]

        response = await client.post(
            "/api/v1/evaluations/compare",
            json={"baseline_run_id": 1, "comparison_run_id": 2},
        )

    assert response.status_code == 409
    assert "completed real evaluation runs" in response.json()["detail"]


@pytest.mark.asyncio
async def test_compare_rejects_incompatible_snapshots(
    client: AsyncClient,
) -> None:
    now = datetime.now(timezone.utc)
    baseline = EvaluationRun(
        id=1,
        dataset_id=1,
        status="COMPLETED",
        metrics={"evaluation_mode": "REAL"},
        snapshot={
            "dataset_fingerprint": "dataset-a",
            "models": ["gpt-4o"],
            "judge_version": "judge-v1",
        },
        created_at=now,
        updated_at=now,
    )
    comparison = EvaluationRun(
        id=2,
        dataset_id=2,
        status="COMPLETED",
        metrics={"evaluation_mode": "REAL"},
        snapshot={
            "dataset_fingerprint": "dataset-b",
            "models": ["gpt-4o"],
            "judge_version": "judge-v1",
        },
        created_at=now,
        updated_at=now,
    )

    with patch(
        "backend.app.api.v1.evaluations.crud_eval.evaluation_run.get",
        new_callable=AsyncMock,
        side_effect=[baseline, comparison],
    ):
        response = await client.post(
            "/api/v1/evaluations/compare",
            json={"baseline_run_id": 1, "comparison_run_id": 2},
        )

    assert response.status_code == 409
    assert "matching dataset snapshots" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "models",
    [
        [],
        ["unsupported-model"],
        ["gpt-4o", "gpt-4o"],
    ],
)
async def test_trigger_rejects_invalid_model_selection(
    client: AsyncClient,
    models: list[str],
) -> None:
    response = await client.post(
        "/api/v1/evaluations/trigger",
        json={"dataset_id": 1, "models": models},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_trigger_rejects_coerced_ids_and_unknown_fields(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/evaluations/trigger",
        json={
            "dataset_id": "1",
            "models": ["gpt-4o"],
            "unexpected": True,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_queue_failure_marks_run_failed(
    client: AsyncClient,
    mock_db: AsyncMock,
) -> None:
    now = datetime.now(timezone.utc)
    dataset = Dataset(
        id=1,
        name="Test DS",
        version="1.0",
        category="general",
        test_cases=[
            CaseModel(
                id=1,
                dataset_id=1,
                question="Question",
                ground_truth="Answer",
                category="general",
                meta_data={},
            )
        ],
    )
    run = EvaluationRun(
        id=10,
        dataset_id=1,
        status="PENDING",
        metrics={},
        snapshot={},
        created_at=now,
        updated_at=now,
    )

    with patch(
        "backend.app.api.v1.evaluations.crud_dataset.dataset.get",
        new_callable=AsyncMock,
        return_value=dataset,
    ), patch(
        "backend.app.api.v1.evaluations.crud_eval.evaluation_run.create",
        new_callable=AsyncMock,
        return_value=run,
    ), patch(
        "backend.app.workers.tasks.run_evaluation_task.apply_async",
        side_effect=ConnectionError("Redis unavailable"),
    ):
        response = await client.post(
            "/api/v1/evaluations/trigger",
            json={"dataset_id": 1, "models": ["gpt-4o"]},
        )

    assert response.status_code == 503
    assert run.status == "FAILED"
    assert run.metrics["queue_error"] == "ConnectionError"
    mock_db.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_cancel_running_evaluation_is_idempotent(
    client: AsyncClient,
) -> None:
    now = datetime.now(timezone.utc)
    run = EvaluationRun(
        id=10,
        dataset_id=1,
        status="RUNNING",
        metrics={"task_id": "task-123"},
        snapshot={},
        created_at=now,
        updated_at=now,
    )

    with patch(
        "backend.app.api.v1.evaluations.crud_eval.evaluation_run.get",
        new_callable=AsyncMock,
        side_effect=[run, run],
    ), patch(
        "backend.app.core.celery_app.celery_app.control.revoke"
    ) as revoke:
        first = await client.post("/api/v1/evaluations/10/cancel")
        second = await client.post("/api/v1/evaluations/10/cancel")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "CANCELLED"
    revoke.assert_called_once_with("task-123", terminate=False)
