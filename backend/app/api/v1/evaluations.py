from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import verify_api_key
from backend.app.crud import dataset as crud_dataset
from backend.app.crud import prompt as crud_prompt
from backend.app.crud import evaluation as crud_eval
from backend.app.crud import regression as crud_reg
from backend.app.models.regression import RegressionReport
from backend.app.schemas import evaluation as schema_eval
from backend.app.schemas import regression as schema_reg

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/trigger", response_model=schema_eval.EvaluationRun, status_code=status.HTTP_202_ACCEPTED)
async def trigger_evaluation(
    trigger_in: schema_eval.EvaluationTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Triggers an evaluation run against a dataset and model suite in the background."""
    # 1. Verify dataset exists
    dataset = await crud_dataset.dataset.get(db, id=trigger_in.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {trigger_in.dataset_id} not found",
        )
    if not dataset.test_cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot trigger evaluation: target dataset has no test cases",
        )

    # 2. Verify prompt exists if provided
    if trigger_in.prompt_id:
        prompt = await crud_prompt.prompt.get(db, id=trigger_in.prompt_id)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {trigger_in.prompt_id} not found",
            )

    # 3. Create the database record
    run_in = schema_eval.EvaluationRunCreate(
        dataset_id=trigger_in.dataset_id,
        prompt_id=trigger_in.prompt_id,
        status="PENDING",
        metrics={},
    )
    run = await crud_eval.evaluation_run.create(db, obj_in=run_in)

    # 4. Dispatch Celery task
    try:
        from backend.app.workers.tasks import run_evaluation_task
        run_evaluation_task.delay(run.id, trigger_in.models)
    except ImportError:
        # Fallback for testing environments without celery fully set up
        pass

    return run


@router.get("/", response_model=List[schema_eval.EvaluationRun])
async def list_evaluation_runs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Lists recent evaluation runs."""
    return await crud_eval.evaluation_run.get_multi(db, skip=skip, limit=limit)


@router.get("/{run_id}", response_model=schema_eval.EvaluationRun)
async def get_evaluation_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetches details of an evaluation run including all child test results."""
    run = await crud_eval.evaluation_run.get(db, id=run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run with ID {run_id} not found",
        )
    return run


# --- Regression Comparisons ---

@router.post("/compare", response_model=schema_reg.RegressionReport, status_code=status.HTTP_201_CREATED)
async def compare_evaluation_runs(
    compare_in: schema_reg.RegressionTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compares a test run to a baseline run and detects performance regressions."""
    # 1. Fetch runs
    baseline = await crud_eval.evaluation_run.get(db, id=compare_in.baseline_run_id)
    comparison = await crud_eval.evaluation_run.get(db, id=compare_in.comparison_run_id)

    if not baseline or not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both of the target evaluation runs not found",
        )

    # 2. Check if comparison exists
    existing = await crud_reg.regression_report.get_by_runs(
        db, baseline_run_id=baseline.id, comparison_run_id=comparison.id
    )
    if existing:
        return existing

    # 3. Compute simple regressions metrics
    # Compare average accuracy, latencies, and cost
    base_acc = baseline.metrics.get("average_accuracy", 0.0)
    comp_acc = comparison.metrics.get("average_accuracy", 0.0)
    score_delta = comp_acc - base_acc

    findings = {
        "baseline_accuracy": base_acc,
        "comparison_accuracy": comp_acc,
        "accuracy_drop": score_delta < 0,
        "latency_delta_ms": comparison.metrics.get("average_latency_ms", 0.0) - baseline.metrics.get("average_latency_ms", 0.0),
        "cost_delta": comparison.metrics.get("total_cost", 0.0) - baseline.metrics.get("total_cost", 0.0),
        "hallucination_rate_delta": comparison.metrics.get("hallucination_rate", 0.0) - baseline.metrics.get("hallucination_rate", 0.0),
    }

    # 4. Save report
    report_in = schema_reg.RegressionReportCreate(
        baseline_run_id=baseline.id,
        comparison_run_id=comparison.id,
        score_delta=score_delta,
        findings=findings,
    )
    
    # Custom CRUD save to bypass missing auto schema mappings
    db_obj = RegressionReport(**report_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/regression/{report_id}", response_model=schema_reg.RegressionReport)
async def get_regression_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetches a specific regression analysis report."""
    result = await db.execute(select(RegressionReport).filter(RegressionReport.id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Regression report with ID {report_id} not found",
        )
    return report
