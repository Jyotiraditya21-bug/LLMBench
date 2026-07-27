from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Test Case Schemas ---

class TestCaseBase(BaseModel):
    question: str = Field(..., min_length=1, max_length=20_000, description="The input prompt/question for the LLM")
    ground_truth: str = Field(..., min_length=1, max_length=20_000, description="The expected ideal answer")
    category: str = Field("general", min_length=1, max_length=100, description="Evaluation category (e.g. factual, reasoning, safety)")
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata tags or parameters")


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    question: Optional[str] = None
    ground_truth: Optional[str] = None
    category: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class TestCase(TestCaseBase):
    id: int
    dataset_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Dataset Schemas ---

class DatasetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Human readable name of the dataset")
    version: str = Field("1.0.0", min_length=1, max_length=50, description="Semver version of the dataset")
    description: Optional[str] = Field(None, max_length=5_000, description="Optional dataset description")
    category: str = Field("general", min_length=1, max_length=100, description="Overall category classification")


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class Dataset(DatasetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    test_cases: List[TestCase] = []

    class Config:
        from_attributes = True
