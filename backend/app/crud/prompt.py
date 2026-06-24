from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.crud.base import CRUDBase
from backend.app.models.prompt import Prompt
from backend.app.schemas.prompt import PromptCreate, PromptUpdate


class CRUDPrompt(CRUDBase[Prompt, PromptCreate, PromptUpdate]):
    """CRUD repository for Prompt templates."""

    async def get_by_name_and_version(
        self, db: AsyncSession, name: str, version: str
    ) -> Optional[Prompt]:
        """Fetch a specific prompt version by template name and version string."""
        result = await db.execute(
            select(self.model).filter(
                self.model.name == name,
                self.model.version == version,
            )
        )
        return result.scalars().first()

    async def get_versions_by_name(self, db: AsyncSession, name: str) -> List[Prompt]:
        """Retrieve all registered versions of a prompt template by name."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.name == name)
            .order_by(self.model.version.desc())
        )
        return result.scalars().all()


prompt = CRUDPrompt(Prompt)
