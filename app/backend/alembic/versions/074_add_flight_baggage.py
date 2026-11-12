"""Add cabin_baggage and checked_baggage to flights.

Free-text allowances as the ticket states them (pieces, weight, size), per leg.
"""

import sqlalchemy as sa
from alembic import op

revision = "074"
down_revision = "073"


def upgrade() -> None:
    op.add_column("flights", sa.Column("cabin_baggage", sa.String(100), nullable=True))
    op.add_column("flights", sa.Column("checked_baggage", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("flights", "checked_baggage")
    op.drop_column("flights", "cabin_baggage")
