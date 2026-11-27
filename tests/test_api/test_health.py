from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_adds_request_id(client: AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "test-id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-id"


@pytest.mark.asyncio
async def test_readiness_reports_component_health(client: AsyncClient) -> None:
    session = AsyncMock()
    session.execute = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)

    redis_client = AsyncMock()
    redis_client.ping.return_value = True
    redis_client.aclose = AsyncMock()

    with patch(
        "backend.app.main.async_session_maker",
        return_value=session_context,
    ), patch(
        "backend.app.main.async_redis.from_url",
        return_value=redis_client,
    ), patch(
        "backend.app.main.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=[{"worker": {"ok": "pong"}}],
    ):
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["components"] == {
        "database": True,
        "redis": True,
        "worker": True,
    }


@pytest.mark.asyncio
async def test_readiness_returns_503_when_dependencies_fail_and_close_raises(
    client: AsyncClient,
) -> None:
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(side_effect=RuntimeError("db down"))
    session_context.__aexit__ = AsyncMock(return_value=None)

    redis_client = AsyncMock()
    redis_client.ping.side_effect = ConnectionError("redis down")
    redis_client.aclose.side_effect = RuntimeError("close failed")

    with patch(
        "backend.app.main.async_session_maker",
        return_value=session_context,
    ), patch(
        "backend.app.main.async_redis.from_url",
        return_value=redis_client,
    ), patch(
        "backend.app.main.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = await client.get("/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["components"] == {
        "database": False,
        "redis": False,
        "worker": False,
    }
