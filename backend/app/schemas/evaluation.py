from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.schemas.dataset import TestCase
from backend.app.schemas.prompt import Prompt


# --- Evaluation Result Schemas ---

SUPPORTED_MODELS = (
    "gpt-4o",
    "gpt-3.5-turbo",
    "claude-3-5-sonnet",
    "claude-3-haiku",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
)
ModelName = Literal[
    "gpt-4o",
    "gpt-3.5-turbo",
    "claude-3-5-sonnet",
    "claude-3-haiku",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]
EvaluationStatus = Literal[
    "PENDING",
    "RUNNING",
    "RETRYING",
    "COMPLETED",
    "DEMO_COMPLETED",
    "FAILED",
    "CANCELLED",
]


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvaluationResultBase(StrictSchema):
    model_name: str = Field(min_length=1, max_length=100)
    raw_output: str = Field(max_length=1_000_000)
    prompt_tokens: int = Field(0, ge=0)
    completion_tokens: int = Field(0, ge=0)
    cost: float = Field(0.0, ge=0, allow_inf_nan=False)
    latency_ms: float = Field(0.0, ge=0, allow_inf_nan=False)
    
    accuracy: Optional[float] = Field(None, ge=1, le=5, allow_inf_nan=False)
    completeness: Optional[float] = Field(None, ge=1, le=5, allow_inf_nan=False)
    hallucination: Optional[float] = Field(None, ge=1, le=5, allow_inf_nan=False)
    tone: Optional[float] = Field(None, ge=1, le=5, allow_inf_nan=False)
    reasoning: Optional[float] = Field(None, ge=1, le=5, allow_inf_nan=False)
    reason: Optional[str] = Field(None, max_length=4_000)


class EvaluationResultCreate(EvaluationResultBase):
    evaluation_run_id: int = Field(gt=0, strict=True)
    test_case_id: int = Field(gt=0, strict=True)


class EvaluationResult(EvaluationResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluation_run_id: int
    test_case_id: int
    created_at: datetime
    updated_at: datetime
    test_case: Optional[TestCase] = None

# --- Evaluation Run Schemas ---

class EvaluationRunBase(StrictSchema):
    dataset_id: int = Field(gt=0)
    prompt_id: Optional[int] = Field(None, gt=0)
    status: EvaluationStatus = "PENDING"
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EvaluationRunCreate(EvaluationRunBase):
    pass


class EvaluationRun(EvaluationRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    results: List[EvaluationResult] = []
    prompt: Optional[Prompt] = None

# --- Trigger & Arena Requests ---

class EvaluationTriggerRequest(StrictSchema):
    dataset_id: int = Field(..., gt=0, strict=True, description="ID of the dataset to evaluate against")
    prompt_id: Optional[int] = Field(None, gt=0, strict=True, description="Optional ID of prompt template. If blank, raw test cases are fed directly.")
    models: List[ModelName] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="Unique supported target models to evaluate",
    )

    @field_validator("models")
    @classmethod
    def models_must_be_unique(cls, models: List[str]) -> List[str]:
        if len(models) != len(set(models)):
            raise ValueError("models must not contain duplicates")
        return models
