"""Add trip participants

Revision ID: 009
Revises: 008
Create Date: 2026-01-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_active to users (existing users are active)
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
    )
    # Add nickname for display (short name like "Аня")
    op.add_column(
        "users",
        sa.Column("nickname", sa.String(50), nullable=True),
    )

    # Add other_participants_count to trips
    op.add_column(
        "trips",
        sa.Column("other_participants_count", sa.Integer(), nullable=True),
    )

    # Create trip_participants junction table
    op.create_table(
        "trip_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trip_id", "user_id", name="uq_trip_participant"),
    )
    op.create_index("ix_trip_participants_trip_id", "trip_participants", ["trip_id"])
    op.create_index("ix_trip_participants_user_id", "trip_participants", ["user_id"])


def downgrade() -> None:
    op.drop_table("trip_participants")
    op.drop_column("trips", "other_participants_count")
    op.drop_column("users", "nickname")
    op.drop_column("users", "is_active")
