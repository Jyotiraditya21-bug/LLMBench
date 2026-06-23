import asyncio
import os
import sys
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import async_session_maker
from backend.app.models.evaluation import EvaluationRun, EvaluationResult
from backend.app.models.dataset import TestCase


async def compile_report(run_id: int) -> str:
    """Queries evaluation statistics and results from DB and compiles a static HTML report page."""
    async with async_session_maker() as db:
        # 1. Fetch Evaluation Run
        run = await db.get(EvaluationRun, run_id)
        if not run:
            print(f"❌ Error: Evaluation run {run_id} not found.")
            sys.exit(1)

        # 2. Fetch nested results
        result_query = await db.execute(
            select(EvaluationResult)
            .filter(EvaluationResult.evaluation_run_id == run_id)
            .order_by(EvaluationResult.id.asc())
        )
        results = result_query.scalars().all()

        # 3. Format result objects to match templates schema
        results_payload = []
        models_evaluated = set()
        
        for r in results:
            models_evaluated.add(r.model_name)
            # Load TestCase details
            tc = await db.get(TestCase, r.test_case_id)
            results_payload.append({
                "model_name": r.model_name,
                "question": tc.question if tc else "N/A",
                "ground_truth": tc.ground_truth if tc else "N/A",
                "raw_output": r.raw_output,
                "accuracy": r.accuracy,
                "completeness": r.completeness,
                "hallucination": r.hallucination,
                "reason": r.reason
            })

        # 4. Set paths for Jinja loader
        # Resolves template relative to workspace/backend/app/templates
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("report.html")

        # 5. Render template
        rendered_html = template.render(
            run_id=run.id,
            dataset_id=run.dataset_id,
            prompt_id=run.prompt_id,
            status=run.status,
            metrics=run.metrics or {},
            created_at=run.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if run.created_at else "N/A",
            models=list(models_evaluated),
            results=results_payload
        )

        # 6. Save to static folder (e.g. docs/index.html)
        # We save under root "docs/" so GitHub Pages serves it by default
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "docs"
        )
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
            
        print(f"🎉 Static HTML report successfully compiled! Saved to: {output_path}")
        return output_path


async def get_latest_run_id() -> int:
    """Fetch the latest completed evaluation run ID from DB."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(EvaluationRun)
            .filter(EvaluationRun.status == "COMPLETED")
            .order_by(EvaluationRun.id.desc())
            .limit(1)
        )
        latest = result.scalars().first()
        if not latest:
            print("❌ Error: No completed evaluation runs found in the database database.")
            sys.exit(1)
        return latest.id


async def main():
    # If run ID passed via argv, compile it; otherwise find the latest completed run
    target_id = None
    if len(sys.argv) > 1:
        try:
            target_id = int(sys.argv[1])
        except ValueError:
            pass

    if target_id is None:
        target_id = await get_latest_run_id()

    await compile_report(target_id)


if __name__ == "__main__":
    asyncio.run(main())
