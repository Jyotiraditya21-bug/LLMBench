from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PromptBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Unique prompt template name")
    version: str = Field(..., min_length=1, max_length=50, description="Prompt version indicator (e.g. V1, V2)")
    system_prompt: Optional[str] = Field(None, max_length=20_000, description="System instructions context")
    user_template: str = Field(..., min_length=1, max_length=20_000, description="User prompt template text, supports double-curly bracket placeholders")
    description: Optional[str] = Field(None, max_length=5_000, description="Optional notes or changelog comment")


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    system_prompt: Optional[str] = None
    user_template: Optional[str] = None
    description: Optional[str] = None


class Prompt(PromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
