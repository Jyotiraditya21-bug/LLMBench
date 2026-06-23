import asyncio
import pytest
from typing import AsyncGenerator, Generator
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.core.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db() -> AsyncMock:
    """Creates an AsyncMock mimicking a SQLAlchemy database AsyncSession."""
    session = AsyncMock()
    # Stub common database methods
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def client(mock_db: AsyncMock) -> Generator[AsyncClient, None, None]:
    """FastAPI AsyncClient fixture overriding get_db with mock_db."""
    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    
    # Initialize HTTPX AsyncClient with auth headers
    headers = {settings.API_KEY_NAME: settings.EVALFORGE_API_KEY}
    client_instance = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers
    )
    yield client_instance
    
    app.dependency_overrides.clear()
