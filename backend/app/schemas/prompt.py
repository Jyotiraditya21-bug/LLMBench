from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PromptBase(StrictSchema):
    name: str = Field(..., min_length=1, max_length=255, description="Unique prompt template name")
    version: str = Field(..., min_length=1, max_length=50, description="Prompt version indicator (e.g. V1, V2)")
    system_prompt: Optional[str] = Field(None, max_length=20_000, description="System instructions context")
    user_template: str = Field(..., min_length=1, max_length=20_000, description="User prompt template text, supports double-curly bracket placeholders")
    description: Optional[str] = Field(None, max_length=5_000, description="Optional notes or changelog comment")


class PromptCreate(PromptBase):
    pass


class PromptUpdate(StrictSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    system_prompt: Optional[str] = Field(None, max_length=20_000)
    user_template: Optional[str] = Field(None, min_length=1, max_length=20_000)
    description: Optional[str] = Field(None, max_length=5_000)


class Prompt(PromptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
