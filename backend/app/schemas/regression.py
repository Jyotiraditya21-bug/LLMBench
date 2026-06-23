from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.evaluation import EvaluationRun


class RegressionReportBase(BaseModel):
    baseline_run_id: int
    comparison_run_id: int
    score_delta: float = 0.0
    findings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RegressionReportCreate(RegressionReportBase):
    pass


class RegressionReport(RegressionReportBase):
    id: int
    created_at: datetime
    updated_at: datetime
    baseline_run: Optional[EvaluationRun] = None
    comparison_run: Optional[EvaluationRun] = None

    class Config:
        from_attributes = True


class RegressionTriggerRequest(BaseModel):
    baseline_run_id: int = Field(..., description="ID of the baseline benchmark evaluation run")
    comparison_run_id: int = Field(..., description="ID of the new/target evaluation run to compare against baseline")
