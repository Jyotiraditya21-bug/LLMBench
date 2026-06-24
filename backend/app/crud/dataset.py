from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.crud.base import CRUDBase
from backend.app.models.dataset import Dataset, TestCase
from backend.app.schemas.dataset import DatasetCreate, DatasetUpdate, TestCaseCreate, TestCaseUpdate


class CRUDDataset(CRUDBase[Dataset, DatasetCreate, DatasetUpdate]):
    """CRUD repository for Dataset operations."""

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Dataset]:
        """Retrieve a dataset by its unique name."""
        result = await db.execute(select(self.model).filter(self.model.name == name))
        return result.scalars().first()


class CRUDTestCase(CRUDBase[TestCase, TestCaseCreate, TestCaseUpdate]):
    """CRUD repository for individual test cases."""

    async def get_by_dataset(
        self, db: AsyncSession, *, dataset_id: int, skip: int = 0, limit: int = 100
    ) -> List[TestCase]:
        """Fetch all test cases associated with a specific dataset."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.dataset_id == dataset_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create_with_dataset(
        self, db: AsyncSession, *, obj_in: TestCaseCreate, dataset_id: int
    ) -> TestCase:
        """Create a new test case linked to a parent dataset."""
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data, dataset_id=dataset_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


dataset = CRUDDataset(Dataset)
test_case = CRUDTestCase(TestCase)
