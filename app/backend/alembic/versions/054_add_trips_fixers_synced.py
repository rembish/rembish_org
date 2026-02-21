"""Add fixers_synced flag to trips

Revision ID: 054
Revises: 053
Create Date: 2026-02-21

Tracks whether fixers were auto-seeded on first info tab view.
"""

import sqlalchemy as sa
from alembic import op

revision = "054"
down_revision = "053"


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column("fixers_synced", sa.Boolean, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("trips", "fixers_synced")
