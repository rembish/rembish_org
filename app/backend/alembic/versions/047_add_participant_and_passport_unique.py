"""Tighten unique constraints on trip_passports

Revision ID: 047
Revises: 046
Create Date: 2026-02-20

DB-02: Enforce one passport per trip — replace composite unique (trip_id, document_id)
       with unique on trip_id alone, matching the app's replace-existing semantics.
"""

from alembic import op

revision = "047"
down_revision = "046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DB-02: one passport per trip — replace (trip_id, document_id) with (trip_id)
    op.drop_constraint("trip_id", "trip_passports", type_="unique")
    op.create_unique_constraint(
        "uq_trip_passports_trip",
        "trip_passports",
        ["trip_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_trip_passports_trip", "trip_passports", type_="unique")
    op.create_unique_constraint(
        "trip_id",
        "trip_passports",
        ["trip_id", "document_id"],
    )
