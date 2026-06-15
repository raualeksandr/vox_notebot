"""Add user profiles and plan fields.

Revision ID: 20260616_0002
Revises: 20260613_0001
Create Date: 2026-06-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260616_0002"
down_revision: str | None = "20260613_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "current_plan",
            sa.String(length=32),
            server_default="free",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "transcription_quality",
            sa.String(length=32),
            server_default="fast",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("profile_type", sa.String(length=64), nullable=True),
        sa.Column("primary_goal", sa.String(length=255), nullable=True),
        sa.Column("preferred_output", sa.String(length=255), nullable=True),
        sa.Column("audio_source", sa.String(length=255), nullable=True),
        sa.Column("quality_preference", sa.String(length=32), nullable=True),
        sa.Column("usage_frequency", sa.String(length=64), nullable=True),
        sa.Column("recommended_plan", sa.String(length=32), nullable=True),
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "transcription_quality")
    op.drop_column("users", "current_plan")
