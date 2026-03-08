"""Initial migration – create reports table.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("fundamentals_data", sa.JSON, nullable=True),
        sa.Column("sentiment_data", sa.JSON, nullable=True),
        sa.Column("technical_data", sa.JSON, nullable=True),
        sa.Column("competitor_data", sa.JSON, nullable=True),
        sa.Column("risk_data", sa.JSON, nullable=True),
        sa.Column("final_analysis", sa.Text, nullable=True),
        sa.Column("pdf_path", sa.String(512), nullable=True),
        sa.Column("errors", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_reports_ticker", "reports", ["ticker"])


def downgrade() -> None:
    op.drop_index("ix_reports_ticker", table_name="reports")
    op.drop_table("reports")
