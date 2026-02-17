"""Add departure/arrival type to trips

Revision ID: 033
Revises: 032
Create Date: 2026-02-17

Adds departure_type and arrival_type columns to trips table
for vacation day calculation (morning/midday/evening).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column(
            "departure_type",
            sa.String(10),
            nullable=False,
            server_default="morning",
        ),
    )
    op.add_column(
        "trips",
        sa.Column(
            "arrival_type",
            sa.String(10),
            nullable=False,
            server_default="evening",
        ),
    )


def downgrade() -> None:
    op.drop_column("trips", "arrival_type")
    op.drop_column("trips", "departure_type")
