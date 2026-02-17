"""Create personal_events table

Revision ID: 034
Revises: 033
Create Date: 2026-02-17

Single-day personal events for calendar conflict detection.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "034"
down_revision: Union[str, None] = "033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "personal_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_date", sa.Date, nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("category", sa.String(20), nullable=False, server_default="other"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("personal_events")
