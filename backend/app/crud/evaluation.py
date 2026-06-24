from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.crud.base import CRUDBase
from backend.app.models.evaluation import EvaluationResult, EvaluationRun
from backend.app.schemas.evaluation import (
    EvaluationResultCreate,
    EvaluationRunCreate,
    EvaluationRunBase,
)


class CRUDEvaluationRun(CRUDBase[EvaluationRun, EvaluationRunCreate, EvaluationRunBase]):
    """CRUD repository for Evaluation Runs."""

    async def update_status(
        self, db: AsyncSession, *, run_id: int, status: str
    ) -> Optional[EvaluationRun]:
        """Atomically update the processing status of an evaluation run (e.g. RUNNING, COMPLETED)."""
        db_obj = await self.get(db, id=run_id)
        if db_obj:
            db_obj.status = status
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

    async def update_metrics(
        self, db: AsyncSession, *, run_id: int, metrics: dict
    ) -> Optional[EvaluationRun]:
        """Insert aggregated metrics summary results for a completed run."""
        db_obj = await self.get(db, id=run_id)
        if db_obj:
            db_obj.metrics = metrics
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj


class CRUDEvaluationResult(CRUDBase[EvaluationResult, EvaluationResultCreate, Any := None]):
    """CRUD repository for granular Evaluation Results."""

    async def get_by_run(
        self, db: AsyncSession, *, evaluation_run_id: int
    ) -> List[EvaluationResult]:
        """Fetch all evaluation results linked to a run."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.evaluation_run_id == evaluation_run_id)
            .order_by(self.model.id.asc())
        )
        return result.scalars().all()


evaluation_run = CRUDEvaluationRun(EvaluationRun)
evaluation_result = CRUDEvaluationResult(EvaluationResult)
