from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.core.security import verify_api_key
from backend.app.crud import dataset as crud_dataset
from backend.app.crud import evaluation as crud_eval
from backend.app.models.dataset import Dataset, TestCase
from backend.app.models.evaluation import EvaluationResult
from agents.rca_agent import analyze_run_failures
from agents.red_team_agent import generate_adversarial_cases

router = APIRouter(dependencies=[Depends(verify_api_key)])


# --- Request/Response Models ---

class RCATriggerRequest(BaseModel):
    run_id: int = Field(..., description="ID of the evaluation run to analyze failures on")


class RedTeamTriggerRequest(BaseModel):
    dataset_id: int = Field(..., description="ID of the seed dataset to red-team")


@router.post("/rca")
async def run_root_cause_analysis(
    request_in: RCATriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves failed evaluation results (accuracy <= 3) and generates a Markdown RCA report."""
    # 1. Fetch evaluation run
    run = await crud_eval.evaluation_run.get(db, id=request_in.run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {request_in.run_id} not found.",
        )

    # 2. Fetch failed results (scoring <= 3 on accuracy)
    result = await db.execute(
        select(EvaluationResult)
        .filter(EvaluationResult.evaluation_run_id == request_in.run_id)
        .filter(EvaluationResult.accuracy <= 3.0)
    )
    failed_results = result.scalars().all()

    # 3. Format failed cases for the agent
    failures_payload = []
    for f in failed_results:
        # Load testcase question/truth
        tc = await db.get(TestCase, f.test_case_id)
        failures_payload.append({
            "question": tc.question if tc else "N/A",
            "ground_truth": tc.ground_truth if tc else "N/A",
            "output": f.raw_output,
            "reason": f.reason
        })

    # 4. Generate report
    report_markdown = await analyze_run_failures(failures_payload)
    return {"run_id": request_in.run_id, "report": report_markdown}


@router.post("/redteam")
async def run_adversarial_generation(
    request_in: RedTeamTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Automatically generates adversarial test cases from seeds and saves them as a new dataset."""
    # 1. Fetch seed dataset
    dataset = await crud_dataset.dataset.get(db, id=request_in.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {request_in.dataset_id} not found.",
        )
    if not dataset.test_cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot Red Team: seed dataset is empty.",
        )

    # 2. Extract test cases
    seed_payload = [{"question": tc.question, "ground_truth": tc.ground_truth} for tc in dataset.test_cases]

    # 3. Run Red Team generation
    adversarial_cases = await generate_adversarial_cases(seed_payload)

    if not adversarial_cases:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Red Team Agent returned empty adversarial cases.",
        )

    # 4. Automatically create new adversarial dataset
    adv_name = f"{dataset.name} [RedTeam-Adversarial]"
    
    # Check if adversarial dataset already exists to avoid name duplication
    existing_result = await db.execute(select(Dataset).filter(Dataset.name == adv_name))
    adv_dataset = existing_result.scalars().first()
    
    if not adv_dataset:
        adv_dataset = Dataset(
            name=adv_name,
            version=dataset.version,
            description=f"Automated Red Team adversarial test suite generated from seed dataset ID: {dataset.id}",
            category="adversarial"
        )
        db.add(adv_dataset)
        await db.commit()
        await db.refresh(adv_dataset)

    # 5. Automatically save adversarial test cases to database
    saved_cases = []
    for ac in adversarial_cases:
        tc_obj = TestCase(
            dataset_id=adv_dataset.id,
            question=ac.get("question"),
            ground_truth=ac.get("ground_truth"),
            category="adversarial",
            meta_data=ac.get("meta_data", {})
        )
        db.add(tc_obj)
        saved_cases.append(tc_obj)
        
    await db.commit()

    return {
        "message": f"Successfully created adversarial suite and saved {len(saved_cases)} test cases.",
        "adversarial_dataset_id": adv_dataset.id,
        "adversarial_dataset_name": adv_dataset.name,
        "cases": [
            {
                "question": c.question,
                "ground_truth": c.ground_truth,
                "meta_data": c.meta_data
            } for c in saved_cases
        ]
    }
