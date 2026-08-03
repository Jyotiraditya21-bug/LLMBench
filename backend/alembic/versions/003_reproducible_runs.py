"""Add immutable run snapshots and version uniqueness.

Revision ID: 003_reproducible_runs
Revises: 002_reliable_evaluation_jobs
Create Date: 2026-07-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "003_reproducible_runs"
down_revision: Union[str, None] = "002_reliable_evaluation_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


json_type = sa.JSON().with_variant(
    postgresql.JSONB(astext_type=sa.Text()),
    "postgresql",
)


def upgrade() -> None:
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "snapshot",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.execute(
        """
        WITH duplicates AS (
            SELECT id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY name, version ORDER BY id
                    ) AS duplicate_number
                FROM datasets
            ) ranked
            WHERE duplicate_number > 1
        )
        UPDATE datasets
        SET version = version || '-legacy-' || datasets.id
        WHERE id IN (SELECT id FROM duplicates)
        """
    )
    op.execute(
        """
        DELETE FROM regression_reports
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM regression_reports
            GROUP BY baseline_run_id, comparison_run_id
        )
        """
    )
    with op.batch_alter_table("datasets") as batch_op:
        batch_op.create_unique_constraint(
            "uq_dataset_name_version",
            ["name", "version"],
        )
    with op.batch_alter_table("regression_reports") as batch_op:
        batch_op.create_unique_constraint(
            "uq_regression_report_run_pair",
            ["baseline_run_id", "comparison_run_id"],
        )
    op.create_index(
        "ix_test_cases_dataset_id",
        "test_cases",
        ["dataset_id"],
    )
    op.create_index(
        "ix_evaluation_runs_dataset_id",
        "evaluation_runs",
        ["dataset_id"],
    )
    op.create_index(
        "ix_evaluation_results_run_case",
        "evaluation_results",
        ["evaluation_run_id", "test_case_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_evaluation_results_run_case", table_name="evaluation_results")
    op.drop_index("ix_evaluation_runs_dataset_id", table_name="evaluation_runs")
    op.drop_index("ix_test_cases_dataset_id", table_name="test_cases")
    with op.batch_alter_table("regression_reports") as batch_op:
        batch_op.drop_constraint(
            "uq_regression_report_run_pair",
            type_="unique",
        )
    with op.batch_alter_table("datasets") as batch_op:
        batch_op.drop_constraint(
            "uq_dataset_name_version",
            type_="unique",
        )
    op.drop_column("evaluation_runs", "snapshot")
