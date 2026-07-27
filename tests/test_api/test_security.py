import pytest
from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.core.security import verify_api_key


@pytest.mark.asyncio
async def test_authentication_fails_closed_when_server_key_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(settings, "EVALFORGE_API_KEY", None)

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key("any-key")

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_authentication_rejects_invalid_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "EVALFORGE_API_KEY", "configured-key")

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key("wrong-key")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authentication_accepts_configured_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "EVALFORGE_API_KEY", "configured-key")

    assert await verify_api_key("configured-key") == "configured-key"
