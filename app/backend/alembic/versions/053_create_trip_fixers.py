"""Create trip_fixers junction table

Revision ID: 053
Revises: 052
Create Date: 2026-02-21

Links fixers to trips for explicit assignment.
"""

import sqlalchemy as sa
from alembic import op

revision = "053"
down_revision = "052"


def upgrade() -> None:
    op.create_table(
        "trip_fixers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fixer_id",
            sa.Integer,
            sa.ForeignKey("fixers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("trip_id", "fixer_id"),
    )
    op.create_index("ix_trip_fixers_trip_id", "trip_fixers", ["trip_id"])
    op.create_index("ix_trip_fixers_fixer_id", "trip_fixers", ["fixer_id"])


def downgrade() -> None:
    op.drop_table("trip_fixers")
