from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Test Case Schemas ---

class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TestCaseBase(StrictSchema):
    question: str = Field(..., min_length=1, max_length=20_000, description="The input prompt/question for the LLM")
    ground_truth: str = Field(..., min_length=1, max_length=20_000, description="The expected ideal answer")
    category: str = Field("general", min_length=1, max_length=100, description="Evaluation category (e.g. factual, reasoning, safety)")
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata tags or parameters")


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(StrictSchema):
    question: Optional[str] = Field(None, min_length=1, max_length=20_000)
    ground_truth: Optional[str] = Field(None, min_length=1, max_length=20_000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    meta_data: Optional[Dict[str, Any]] = None


class TestCase(TestCaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    created_at: datetime
    updated_at: datetime

# --- Dataset Schemas ---

class DatasetBase(StrictSchema):
    name: str = Field(..., min_length=1, max_length=255, description="Human readable name of the dataset")
    version: str = Field("1.0.0", min_length=1, max_length=50, description="Semver version of the dataset")
    description: Optional[str] = Field(None, max_length=5_000, description="Optional dataset description")
    category: str = Field("general", min_length=1, max_length=100, description="Overall category classification")


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(StrictSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=5_000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)


class Dataset(DatasetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    test_cases: List[TestCase] = Field(default_factory=list)
