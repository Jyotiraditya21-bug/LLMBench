from typing import Optional
from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Prompt(Base):
    """Represents prompt templates and system guidelines versioned in the database.

    Enables systematic A/B benchmarking across versions (e.g. Prompt V1 vs V2 vs V3).
    """

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_template: Mapped[str] = mapped_column(Text, nullable=False)  # e.g., "Answer the question: {{question}}"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        # Ensure unique name + version combination
        UniqueConstraint("name", "version", name="uq_prompt_name_version"),
    )
