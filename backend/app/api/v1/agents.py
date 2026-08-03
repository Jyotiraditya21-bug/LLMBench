from typing import Any, Dict

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.celery_app import celery_app
from backend.app.core.database import get_db
from backend.app.core.security import verify_api_key
from backend.app.crud import dataset as crud_dataset
from backend.app.crud import evaluation as crud_eval
from backend.app.workers.agent_tasks import run_rca_task, run_redteam_task


router = APIRouter(dependencies=[Depends(verify_api_key)])


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RCATriggerRequest(StrictRequest):
    run_id: int = Field(..., gt=0, strict=True)


class RedTeamTriggerRequest(StrictRequest):
    dataset_id: int = Field(..., gt=0, strict=True)


def _dispatch(task, args: list[int]) -> Dict[str, str]:
    try:
        result = task.apply_async(args=args)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent queue is unavailable",
        ) from exc
    return {"job_id": result.id, "status": "PENDING"}


@router.post("/rca", status_code=status.HTTP_202_ACCEPTED)
async def run_root_cause_analysis(
    request_in: RCATriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    run = await crud_eval.evaluation_run.get(db, id=request_in.run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {request_in.run_id} not found",
        )
    return _dispatch(run_rca_task, [request_in.run_id])


@router.post("/redteam", status_code=status.HTTP_202_ACCEPTED)
async def run_adversarial_generation(
    request_in: RedTeamTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    dataset = await crud_dataset.dataset.get(db, id=request_in.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {request_in.dataset_id} not found",
        )
    if not dataset.test_cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot red-team an empty dataset",
        )
    return _dispatch(run_redteam_task, [request_in.dataset_id])


@router.get("/jobs/{job_id}")
async def get_agent_job(job_id: str):
    if not job_id or len(job_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid job ID",
        )
    result = AsyncResult(job_id, app=celery_app)
    payload: Dict[str, Any] = {"job_id": job_id, "status": result.state}
    if result.successful():
        payload["result"] = result.result
    elif result.failed():
        payload["error"] = "Agent job failed"
    return payload
