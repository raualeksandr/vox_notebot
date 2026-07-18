"""add consent_accepted_at to users

Revision ID: 20260718_0004
Revises: 20260621_0003
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260718_0004"
down_revision: str | None = "20260621_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("consent_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "consent_accepted_at")
