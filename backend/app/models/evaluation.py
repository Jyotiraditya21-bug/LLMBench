from typing import List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class EvaluationRun(Base):
    """Represents a benchmark execution suite.

    Tracks a set of models run against a dataset using a given prompt.
    """

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    prompt_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    
    # Store aggregated scores (e.g., {"accuracy": 4.5, "hallucination_rate": 0.1, "total_cost": 0.25})
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset")
    prompt: Mapped[Optional["Prompt"]] = relationship("Prompt", lazy="selectin")
    results: Mapped[List["EvaluationResult"]] = relationship(
        "EvaluationResult",
        back_populates="evaluation_run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EvaluationResult(Base):
    """The outcome of a single model's response to an individual test case.

    Captures latency, tokens, costs, raw generated text, and strict judge scores.
    """

    evaluation_run_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    # Text Generation Output
    raw_output: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Performance & Cost Analytics
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # LLM-as-a-Judge Scores (Scored 1-5 or custom scale)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completeness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hallucination: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tone: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reasoning: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # LLM Judge qualitative logic

    # Relationships
    evaluation_run: Mapped["EvaluationRun"] = relationship("EvaluationRun", back_populates="results")
    test_case: Mapped["TestCase"] = relationship("TestCase", lazy="selectin")
