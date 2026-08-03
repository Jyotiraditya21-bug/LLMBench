"""Add evaluation result idempotency constraint.

Revision ID: 002_reliable_evaluation_jobs
Revises: 001_initial_schema
Create Date: 2026-07-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "002_reliable_evaluation_jobs"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep the oldest result if a V1 retry already produced duplicate rows.
    op.execute(
        """
        DELETE FROM evaluation_results
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM evaluation_results
            GROUP BY evaluation_run_id, test_case_id, model_name
        )
        """
    )
    with op.batch_alter_table("evaluation_results") as batch_op:
        batch_op.create_unique_constraint(
            "uq_evaluation_result_run_case_model",
            ["evaluation_run_id", "test_case_id", "model_name"],
        )


def downgrade() -> None:
    with op.batch_alter_table("evaluation_results") as batch_op:
        batch_op.drop_constraint(
            "uq_evaluation_result_run_case_model",
            type_="unique",
        )
