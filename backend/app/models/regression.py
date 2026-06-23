from typing import Optional
from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class RegressionReport(Base):
    """Stores regression reports generated when comparing two evaluation runs.

    Helps track performance drops, hallucination rate spikes, cost, and latency deltas.
    """

    baseline_run_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    comparison_run_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Quantitative comparison delta (comparison score - baseline score)
    score_delta: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Qualitative and structured metrics breakdown (e.g. {"latency_increase_percent": 15.5, "hallucinated_questions": [4, 12]})
    findings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, nullable=True)

    # Relationships
    baseline_run: Mapped["EvaluationRun"] = relationship(
        "EvaluationRun",
        foreign_keys=[baseline_run_id],
        lazy="selectin",
    )
    comparison_run: Mapped["EvaluationRun"] = relationship(
        "EvaluationRun",
        foreign_keys=[comparison_run_id],
        lazy="selectin",
    )

