import os
import sys
from types import ModuleType
from typing import Any, Dict, List, Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    # Dynamically inject dummy anthropic module to satisfy imports and mock patches
    dummy_anthropic = ModuleType("anthropic")
    
    class AsyncAnthropic:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
    class NotGiven:
        pass
        
    dummy_anthropic.AsyncAnthropic = AsyncAnthropic
    dummy_anthropic.NotGiven = NotGiven
    sys.modules["anthropic"] = dummy_anthropic
    HAS_ANTHROPIC = False

from pydantic import AnyHttpUrl, BeforeValidator, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.app.core.google_client import HAS_GOOGLE_GENAI


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LLMBench"
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:8000,http://localhost:7860"
    )

    # API Security
    API_KEY_NAME: str = "X-API-Key"
    EVALFORGE_API_KEY: Optional[str] = None

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "evalforge"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: Any) -> Any:
        if isinstance(v, str) and v:
            return v
        
        import os
        if os.getenv("SPACE_ID") or os.getenv("USE_SQLITE") == "true":
            return "sqlite+aiosqlite:////tmp/evalforge.db"

        data = info.data
        return f"postgresql+asyncpg://{data.get('POSTGRES_USER')}:{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_SERVER')}:{data.get('POSTGRES_PORT')}/{data.get('POSTGRES_DB')}"

    # Redis (Celery broker and backend)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: Any) -> Any:
        if isinstance(v, str) and v:
            return v
        data = info.data
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/0"

    # AI Model Providers APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    HAS_ANTHROPIC: bool = HAS_ANTHROPIC
    HAS_GOOGLE_GENAI: bool = HAS_GOOGLE_GENAI
    DEMO_MODE: bool = False
    MODEL_CALL_TIMEOUT_SECONDS: int = Field(120, ge=1, le=600)
    EVALUATION_TASK_SOFT_LIMIT_SECONDS: int = Field(1_800, ge=60)
    EVALUATION_TASK_HARD_LIMIT_SECONDS: int = Field(1_860, ge=60)
    EVALUATION_TASK_MAX_RETRIES: int = Field(2, ge=0, le=10)
    EVALUATION_MAX_CONCURRENCY: int = Field(4, ge=1, le=32)
    OPENAI_MAX_CONCURRENCY: int = Field(2, ge=1, le=16)
    ANTHROPIC_MAX_CONCURRENCY: int = Field(2, ge=1, le=16)
    GEMINI_MAX_CONCURRENCY: int = Field(2, ge=1, le=16)
    READINESS_REQUIRE_WORKER: bool = True

    @model_validator(mode="after")
    def validate_task_time_limits(self) -> "Settings":
        if (
            self.EVALUATION_TASK_HARD_LIMIT_SECONDS
            <= self.EVALUATION_TASK_SOFT_LIMIT_SECONDS
        ):
            raise ValueError(
                "EVALUATION_TASK_HARD_LIMIT_SECONDS must exceed the soft limit"
            )
        return self

    # Observability (Optional integrations)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "evalforge"


settings = Settings()
