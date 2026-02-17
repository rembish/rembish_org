"""Add arrival_date to flights

Revision ID: 038
Revises: 037
Create Date: 2026-02-17

For overnight/long-haul flights where arrival date differs from departure.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "038"
down_revision: Union[str, None] = "037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("flights", sa.Column("arrival_date", sa.Date, nullable=True))


def downgrade() -> None:
    op.drop_column("flights", "arrival_date")
