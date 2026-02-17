"""Add end_date to personal_events

Revision ID: 035
Revises: 034
Create Date: 2026-02-17

Support multi-day events (e.g., 3-day comic con).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "035"
down_revision: Union[str, None] = "034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "personal_events",
        sa.Column("end_date", sa.Date, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("personal_events", "end_date")
