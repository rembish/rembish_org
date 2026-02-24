"""Add is_deleted column to drone_flights

Revision ID: 061
Revises: 060
Create Date: 2026-02-24

Soft-delete flag to permanently mark flights as junk without hard-deleting,
so the seed script's dedup logic still sees the source_file and won't reimport.
"""

import sqlalchemy as sa
from alembic import op

revision = "061"
down_revision = "060"


def upgrade() -> None:
    op.add_column(
        "drone_flights",
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("drone_flights", "is_deleted")
