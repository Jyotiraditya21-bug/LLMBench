from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.evaluation import EvaluationRun


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegressionReportBase(StrictSchema):
    baseline_run_id: int = Field(gt=0)
    comparison_run_id: int = Field(gt=0)
    score_delta: float = Field(0.0, allow_inf_nan=False)
    findings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RegressionReportCreate(RegressionReportBase):
    pass


class RegressionReport(RegressionReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    baseline_run: Optional[EvaluationRun] = None
    comparison_run: Optional[EvaluationRun] = None

class RegressionTriggerRequest(StrictSchema):
    baseline_run_id: int = Field(..., gt=0, strict=True, description="ID of the baseline benchmark evaluation run")
    comparison_run_id: int = Field(..., gt=0, strict=True, description="ID of the new/target evaluation run to compare against baseline")
