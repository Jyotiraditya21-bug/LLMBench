from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.models import (
    Dataset,
    EvaluationResult,
    EvaluationRun,
    TestCase as CaseModel,
)
from backend.app.models.base import Base
from backend.app.workers import tasks


@pytest.mark.asyncio
async def test_worker_executes_snapshot_and_persists_one_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        dataset = Dataset(
            name="Snapshot dataset",
            version="1.0.0",
            category="reasoning",
        )
        session.add(dataset)
        await session.flush()
        test_case = CaseModel(
            dataset_id=dataset.id,
            question="Live question",
            ground_truth="Live answer",
            category="reasoning",
            meta_data={},
        )
        session.add(test_case)
        await session.flush()
        run = EvaluationRun(
            dataset_id=dataset.id,
            status="PENDING",
            metrics={},
            snapshot={
                "dataset": {
                    "test_cases": [
                        {
                            "id": test_case.id,
                            "question": "Snapshotted question",
                            "ground_truth": "Snapshotted answer",
                            "category": "reasoning",
                            "meta_data": {},
                        }
                    ]
                },
                "prompt": None,
                "models": ["gpt-4o"],
            },
        )
        session.add(run)
        await session.commit()
        run_id = run.id

    monkeypatch.setattr(tasks, "async_session_maker", session_factory)
    target = {
        "output": "Snapshotted answer",
        "prompt_tokens": 5,
        "completion_tokens": 3,
        "cost": 0.001,
        "latency_ms": 10.0,
        "usage_estimated": False,
        "is_mock": False,
    }
    judge = {
        "accuracy": 5.0,
        "completeness": 5.0,
        "hallucination": 5.0,
        "tone": 5.0,
        "reasoning": 5.0,
        "reason": "Correct",
        "is_mock": False,
    }
    with patch.object(
        tasks,
        "call_target_llm",
        new_callable=AsyncMock,
        return_value=target,
    ) as target_call, patch.object(
        tasks,
        "evaluate_with_judge",
        new_callable=AsyncMock,
        return_value=judge,
    ):
        result = await tasks.async_run_evaluation(run_id, ["gpt-4o"])

    assert "completed successfully" in result
    assert target_call.await_args.kwargs["prompt_text"] == "Snapshotted question"
    async with session_factory() as session:
        stored_run = await session.get(EvaluationRun, run_id)
        count = await session.scalar(select(func.count(EvaluationResult.id)))
        assert stored_run.status == "COMPLETED"
        assert stored_run.metrics["progress"] == {"completed": 1, "total": 1}
        assert count == 1

    await engine.dispose()
