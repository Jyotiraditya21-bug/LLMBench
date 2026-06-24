from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from backend.app.models.dataset import Dataset
from backend.app.models.prompt import Prompt
from backend.app.models.evaluation import EvaluationRun
from backend.app.models.regression import RegressionReport


@pytest.mark.asyncio
async def test_trigger_evaluation_success(client: AsyncClient, mock_db: AsyncMock) -> None:
    """Asserts that triggering evaluation with valid data schedules task and returns HTTP 202."""
    now = datetime.now(timezone.utc)
    mock_dataset = Dataset(id=1, name="Test DS", version="1.0", test_cases=[AsyncMock()])
    mock_prompt = Prompt(id=2, name="Test Prompt", version="1.0")
    mock_run = EvaluationRun(id=10, dataset_id=1, prompt_id=2, status="PENDING", created_at=now, updated_at=now)

    with patch("backend.app.api.v1.evaluations.crud_dataset.dataset.get", new_callable=AsyncMock) as mock_get_ds, \
         patch("backend.app.api.v1.evaluations.crud_prompt.prompt.get", new_callable=AsyncMock) as mock_get_pr, \
         patch("backend.app.api.v1.evaluations.crud_eval.evaluation_run.create", new_callable=AsyncMock) as mock_create_run, \
         patch("backend.app.workers.tasks.run_evaluation_task.delay") as mock_celery_delay:
        
        mock_get_ds.return_value = mock_dataset
        mock_get_pr.return_value = mock_prompt
        mock_create_run.return_value = mock_run

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
        mock_celery_delay.assert_called_once_with(10, ["gpt-4o"])


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
