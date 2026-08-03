import asyncio
from typing import Any, Dict

from sqlalchemy import select

from agents.rca_agent import analyze_run_failures
from agents.red_team_agent import generate_adversarial_cases
from backend.app.core.celery_app import celery_app
from backend.app.core.database import async_session_maker
from backend.app.models.dataset import Dataset, TestCase
from backend.app.models.evaluation import EvaluationResult, EvaluationRun


@celery_app.task(
    name="backend.app.workers.agent_tasks.run_rca_task",
    soft_time_limit=600,
    time_limit=660,
)
def run_rca_task(run_id: int) -> Dict[str, Any]:
    return asyncio.run(_run_rca(run_id))


async def _run_rca(run_id: int) -> Dict[str, Any]:
    async with async_session_maker() as db:
        run = await db.get(EvaluationRun, run_id)
        if not run:
            raise ValueError(f"Evaluation run {run_id} not found")
        result = await db.execute(
            select(EvaluationResult)
            .where(EvaluationResult.evaluation_run_id == run_id)
            .where(EvaluationResult.accuracy <= 3.0)
        )
        failed_results = result.scalars().all()
        failures = []
        for failed in failed_results:
            test_case = await db.get(TestCase, failed.test_case_id)
            failures.append(
                {
                    "question": test_case.question if test_case else "N/A",
                    "ground_truth": (
                        test_case.ground_truth if test_case else "N/A"
                    ),
                    "output": failed.raw_output,
                    "reason": failed.reason,
                }
            )
    report = await analyze_run_failures(failures)
    return {"run_id": run_id, "report": report}


@celery_app.task(
    name="backend.app.workers.agent_tasks.run_redteam_task",
    soft_time_limit=600,
    time_limit=660,
)
def run_redteam_task(dataset_id: int) -> Dict[str, Any]:
    return asyncio.run(_run_redteam(dataset_id))


async def _run_redteam(dataset_id: int) -> Dict[str, Any]:
    async with async_session_maker() as db:
        dataset = await db.get(Dataset, dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        seed_result = await db.execute(
            select(TestCase)
            .where(TestCase.dataset_id == dataset_id)
            .order_by(TestCase.id)
            .limit(100)
        )
        seeds = seed_result.scalars().all()
        if not seeds:
            raise ValueError("Seed dataset is empty")
        adversarial_cases = await generate_adversarial_cases(
            [
                {
                    "question": item.question,
                    "ground_truth": item.ground_truth,
                }
                for item in seeds
            ]
        )
        if not adversarial_cases:
            raise ValueError("Red Team agent returned no cases")

        version = f"{dataset.version}-redteam"
        existing = await db.scalar(
            select(Dataset).where(
                Dataset.name == f"{dataset.name} [RedTeam-Adversarial]",
                Dataset.version == version,
            )
        )
        if existing:
            raise ValueError(
                "An adversarial dataset already exists for this dataset version"
            )
        adversarial_dataset = Dataset(
            name=f"{dataset.name} [RedTeam-Adversarial]",
            version=version,
            description=(
                "Automated adversarial suite generated from dataset "
                f"{dataset.id}"
            ),
            category="adversarial",
        )
        db.add(adversarial_dataset)
        await db.flush()
        records = [
            TestCase(
                dataset_id=adversarial_dataset.id,
                question=item["question"],
                ground_truth=item["ground_truth"],
                category="adversarial",
                meta_data=item.get("meta_data", {}),
            )
            for item in adversarial_cases
        ]
        db.add_all(records)
        await db.commit()
        return {
            "message": (
                f"Created {len(records)} adversarial test cases."
            ),
            "adversarial_dataset_id": adversarial_dataset.id,
            "adversarial_dataset_name": adversarial_dataset.name,
            "cases": adversarial_cases,
        }
