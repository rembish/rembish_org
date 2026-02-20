"""Add unique constraint on trip_destinations (trip_id, tcc_destination_id)

Revision ID: 046
Revises: 045
Create Date: 2026-02-20

Prevents duplicate destination entries per trip.
"""

from alembic import op

revision = "046"
down_revision = "045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_trip_destinations_trip_tcc",
        "trip_destinations",
        ["trip_id", "tcc_destination_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_trip_destinations_trip_tcc", "trip_destinations", type_="unique")
