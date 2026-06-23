from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PromptBase(BaseModel):
    name: str = Field(..., description="Unique name identify the prompt template")
    version: str = Field(..., description="Prompt version indicator (e.g. V1, V2)")
    system_prompt: Optional[str] = Field(None, description="System instructions context")
    user_template: str = Field(..., description="User prompt template text, supports double-curly brackets placeholders")
    description: Optional[str] = Field(None, description="Optional notes or changelog comment")


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
