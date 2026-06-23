from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.dataset import TestCase
from backend.app.schemas.prompt import Prompt


# --- Evaluation Result Schemas ---

class EvaluationResultBase(BaseModel):
    model_name: str
    raw_output: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    
    accuracy: Optional[float] = None
    completeness: Optional[float] = None
    hallucination: Optional[float] = None
    tone: Optional[float] = None
    reasoning: Optional[float] = None
    reason: Optional[str] = None


class EvaluationResultCreate(EvaluationResultBase):
    evaluation_run_id: int
    test_case_id: int


class EvaluationResult(EvaluationResultBase):
    id: int
    evaluation_run_id: int
    test_case_id: int
    created_at: datetime
    updated_at: datetime
    test_case: Optional[TestCase] = None

    class Config:
        from_attributes = True


# --- Evaluation Run Schemas ---

class EvaluationRunBase(BaseModel):
    dataset_id: int
    prompt_id: Optional[int] = None
    status: str = "PENDING"
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EvaluationRunCreate(EvaluationRunBase):
    pass


class EvaluationRun(EvaluationRunBase):
    id: int
    created_at: datetime
    updated_at: datetime
    results: List[EvaluationResult] = []
    prompt: Optional[Prompt] = None

    class Config:
        from_attributes = True


# --- Trigger & Arena Requests ---

class EvaluationTriggerRequest(BaseModel):
    dataset_id: int = Field(..., description="ID of the dataset to evaluate against")
    prompt_id: Optional[int] = Field(None, description="Optional ID of prompt template. If blank, raw test cases are fed directly.")
    models: List[str] = Field(..., description="List of target LLM model names to evaluate (e.g. ['gpt-4o', 'claude-3-5-sonnet', 'gemini-1.5-flash'])")
