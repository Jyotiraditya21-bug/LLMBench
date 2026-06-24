from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.crud.base import CRUDBase
from backend.app.models.regression import RegressionReport
from backend.app.schemas.regression import RegressionReportCreate


class CRUDRegressionReport(CRUDBase[RegressionReport, RegressionReportCreate, Any := None]):
    """CRUD repository for Regression Reports."""

    async def get_by_runs(
        self, db: AsyncSession, *, baseline_run_id: int, comparison_run_id: int
    ) -> Optional[RegressionReport]:
        """Retrieve a regression report comparing two specific runs if it already exists."""
        result = await db.execute(
            select(self.model).filter(
                self.model.baseline_run_id == baseline_run_id,
                self.model.comparison_run_id == comparison_run_id,
            )
        )
        return result.scalars().first()


regression_report = CRUDRegressionReport(RegressionReport)
