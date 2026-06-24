import asyncio
from backend.app.core.database import async_session_maker, init_db, drop_db
from backend.app.models.dataset import Dataset, TestCase
from backend.app.models.prompt import Prompt
from backend.app.models.evaluation import EvaluationRun, EvaluationResult

async def seed():
    await drop_db()
    await init_db()
    async with async_session_maker() as db:
        # Create dataset
        ds = Dataset(
            name="Core Reasoning QA",
            version="1.0.0",
            description="General test cases for reasoning and correctness",
            category="reasoning"
        )
        db.add(ds)
        await db.commit()
        await db.refresh(ds)
        print(f"Created dataset ID: {ds.id}")

        # Create test cases
        tc1 = TestCase(
            dataset_id=ds.id,
            question="What is the square root of 144?",
            ground_truth="12",
            category="reasoning",
            meta_data={"difficulty": "easy"}
        )
        tc2 = TestCase(
            dataset_id=ds.id,
            question="If a train travels at 60 mph, how far does it travel in 2.5 hours?",
            ground_truth="150 miles",
            category="reasoning",
            meta_data={"difficulty": "medium"}
        )
        db.add(tc1)
        db.add(tc2)
        
        # Create Prompt
        p = Prompt(
            name="Reasoning Direct Instruction",
            version="1.0",
            system_prompt="Be concise and accurate.",
            user_template="Answer the following question: {{question}}",
            description="V1 release template"
        )
        db.add(p)
        
        await db.commit()
        await db.refresh(p)
        print(f"Created test cases and prompt ID: {p.id}")

        # Let's seed an evaluation run
        run = EvaluationRun(
            dataset_id=ds.id,
            prompt_id=p.id,
            status="COMPLETED",
            metrics={
                "total_results": 2,
                "total_cost": 0.0012,
                "average_latency_ms": 1240.0,
                "average_accuracy": 4.5,
                "average_completeness": 4.2,
                "average_hallucination": 4.8,
                "average_tone": 4.0,
                "average_reasoning": 4.6,
                "hallucination_rate": 0.0
            }
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        print(f"Created completed evaluation run ID: {run.id}")

        res1 = EvaluationResult(
            evaluation_run_id=run.id,
            test_case_id=tc1.id,
            model_name="claude-3-haiku",
            raw_output="The square root of 144 is 12.",
            prompt_tokens=15,
            completion_tokens=10,
            cost=0.0001,
            latency_ms=800.0,
            accuracy=5.0,
            completeness=5.0,
            hallucination=5.0,
            tone=4.0,
            reasoning=5.0,
            reason="The output is exact and correct."
        )
        res2 = EvaluationResult(
            evaluation_run_id=run.id,
            test_case_id=tc2.id,
            model_name="claude-3-haiku",
            raw_output="It will travel 150 miles.",
            prompt_tokens=25,
            completion_tokens=8,
            cost=0.00015,
            latency_ms=900.0,
            accuracy=4.0,
            completeness=4.0,
            hallucination=4.5,
            tone=4.0,
            reasoning=4.0,
            reason="Correct math, though could state units clearly."
        )
        db.add(res1)
        db.add(res2)
        await db.commit()
        print("Seeded database successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
