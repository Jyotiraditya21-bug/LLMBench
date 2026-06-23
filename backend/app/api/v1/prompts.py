from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import verify_api_key
from backend.app.crud import prompt as crud_prompt
from backend.app.schemas import prompt as schema_prompt

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/", response_model=schema_prompt.Prompt, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_in: schema_prompt.PromptCreate,
    db: AsyncSession = Depends(get_db),
):
    """Registers a new prompt template version."""
    existing = await crud_prompt.prompt.get_by_name_and_version(
        db, name=prompt_in.name, version=prompt_in.version
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prompt template '{prompt_in.name}' version '{prompt_in.version}' already exists.",
        )
    return await crud_prompt.prompt.create(db, obj_in=prompt_in)


@router.get("/", response_model=List[schema_prompt.Prompt])
async def list_prompts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Lists registered prompt templates."""
    return await crud_prompt.prompt.get_multi(db, skip=skip, limit=limit)


@router.get("/{prompt_id}", response_model=schema_prompt.Prompt)
async def get_prompt(
    prompt_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetches full template prompt details by ID."""
    db_prompt = await crud_prompt.prompt.get(db, id=prompt_id)
    if not db_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found",
        )
    return db_prompt


@router.get("/name/{name}", response_model=List[schema_prompt.Prompt])
async def get_prompt_versions(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all registered version variations of a given prompt name."""
    return await crud_prompt.prompt.get_versions_by_name(db, name=name)


@router.delete("/{prompt_id}", status_code=status.HTTP_200_OK)
async def delete_prompt(
    prompt_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Deletes a prompt template version from registry."""
    db_prompt = await crud_prompt.prompt.get(db, id=prompt_id)
    if not db_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found",
        )
    await crud_prompt.prompt.remove(db, id=prompt_id)
    return {"message": f"Prompt {prompt_id} deleted successfully"}
