from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import verify_api_key
from backend.app.crud import dataset as crud_dataset
from backend.app.schemas import dataset as schema_dataset

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/", response_model=schema_dataset.Dataset, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_in: schema_dataset.DatasetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Creates a new evaluation dataset folder record."""
    return await crud_dataset.dataset.create(db, obj_in=dataset_in)


@router.get("/", response_model=List[schema_dataset.Dataset])
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Lists all available evaluation datasets."""
    return await crud_dataset.dataset.get_multi(db, skip=skip, limit=limit)


@router.get("/{dataset_id}", response_model=schema_dataset.Dataset)
async def get_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetches a specific dataset including nested test cases."""
    db_dataset = await crud_dataset.dataset.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    return db_dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_200_OK)
async def delete_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Deletes a dataset and all associated test cases."""
    db_dataset = await crud_dataset.dataset.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    await crud_dataset.dataset.remove(db, id=dataset_id)
    return {"message": f"Dataset {dataset_id} deleted successfully"}


# --- TestCase Sub-endpoints ---

@router.post("/{dataset_id}/testcases", response_model=schema_dataset.TestCase, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    dataset_id: int,
    test_case_in: schema_dataset.TestCaseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Appends an individual evaluation test case to a dataset."""
    db_dataset = await crud_dataset.dataset.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    return await crud_dataset.test_case.create_with_dataset(
        db, obj_in=test_case_in, dataset_id=dataset_id
    )


@router.post("/{dataset_id}/testcases/batch", status_code=status.HTTP_201_CREATED)
async def create_test_cases_batch(
    dataset_id: int,
    test_cases_in: List[schema_dataset.TestCaseCreate],
    db: AsyncSession = Depends(get_db),
):
    """Batch imports an array of JSON test cases into a dataset."""
    db_dataset = await crud_dataset.dataset.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    
    created_items = []
    for tc in test_cases_in:
        item = await crud_dataset.test_case.create_with_dataset(
            db, obj_in=tc, dataset_id=dataset_id
        )
        created_items.append(item)
        
    return {
        "message": f"Successfully imported {len(created_items)} test cases",
        "dataset_id": dataset_id
    }


@router.get("/{dataset_id}/testcases", response_model=List[schema_dataset.TestCase])
async def list_test_cases(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Lists test cases within a dataset."""
    db_dataset = await crud_dataset.dataset.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found",
        )
    return await crud_dataset.test_case.get_by_dataset(
        db, dataset_id=dataset_id, skip=skip, limit=limit
    )


@router.delete("/{dataset_id}/testcases/{test_case_id}", status_code=status.HTTP_200_OK)
async def delete_test_case(
    dataset_id: int,
    test_case_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Deletes a specific test case from a dataset."""
    db_tc = await crud_dataset.test_case.get(db, id=test_case_id)
    if not db_tc or db_tc.dataset_id != dataset_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {test_case_id} not found under dataset {dataset_id}",
        )
    await crud_dataset.test_case.remove(db, id=test_case_id)
    return {"message": f"Test case {test_case_id} removed successfully"}
