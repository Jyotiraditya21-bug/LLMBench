from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings

# Create database engine with async pg driver
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True to output raw SQL queries to console
    future=True,
    pool_pre_ping=True,  # Check connection health before executing queries
)

# Async session factory
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to yield database sessions.

    Ensures proper cleanup and rollback if errors occur.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Auto-creates all tables in the target database schema."""
    # Import models here to ensure they are registered on the Base metadata
    from backend.app.models.dataset import Dataset, TestCase
    from backend.app.models.prompt import Prompt
    from backend.app.models.evaluation import EvaluationRun, EvaluationResult
    from backend.app.models.regression import RegressionReport
    from backend.app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

