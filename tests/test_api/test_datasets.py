from datetime import datetime, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from backend.app.models.dataset import Dataset
from backend.app.schemas import dataset as schema_dataset


@pytest.mark.asyncio
async def test_create_dataset_success(client: AsyncClient) -> None:
    """Asserts that a valid dataset payload returns HTTP 201 and correct mock response."""
    now = datetime.now(timezone.utc)
    mock_dataset_db = Dataset(
        id=1,
        name="Test QA Dataset",
        version="1.0.0",
        description="Verify prompt safety",
        category="safety",
        created_at=now,
        updated_at=now
    )

    with patch("backend.app.api.v1.datasets.crud_dataset.dataset.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_dataset_db

        payload = {
            "name": "Test QA Dataset",
            "version": "1.0.0",
            "description": "Verify prompt safety",
            "category": "safety"
        }
        response = await client.post("/api/v1/datasets/", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test QA Dataset"
        assert data["id"] == 1
        assert data["category"] == "safety"


@pytest.mark.asyncio
async def test_list_datasets(client: AsyncClient) -> None:
    """Asserts listing datasets calls get_multi and returns dataset schemas."""
    now = datetime.now(timezone.utc)
    mock_list = [
        Dataset(id=1, name="DS1", version="1.0", description="Desc1", category="factual", created_at=now, updated_at=now),
        Dataset(id=2, name="DS2", version="2.0", description="Desc2", category="reasoning", created_at=now, updated_at=now)
    ]

    with patch("backend.app.api.v1.datasets.crud_dataset.dataset.get_multi", new_callable=AsyncMock) as mock_multi:
        mock_multi.return_value = mock_list

        response = await client.get("/api/v1/datasets/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "DS1"
        assert data[1]["name"] == "DS2"


@pytest.mark.asyncio
async def test_unauthorized_access() -> None:
    """Asserts that requests missing X-API-Key are blocked with HTTP 403."""
    from backend.app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as autoless_client:
        response = await autoless_client.get("/api/v1/datasets/")
        assert response.status_code == 403
        assert "credentials missing" in response.json()["detail"].lower()
