"""Add performance indexes for travel queries

Revision ID: 025
Revises: 024
Create Date: 2026-01-28
"""

from typing import Sequence, Union

from alembic import op


revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Index on tcc_destinations.un_country_id - heavily used in JOINs
    op.create_index(
        "ix_tcc_destinations_un_country_id",
        "tcc_destinations",
        ["un_country_id"],
    )
    # Index on trips.end_date - used in date range filters
    op.create_index(
        "ix_trips_end_date",
        "trips",
        ["end_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_trips_end_date", table_name="trips")
    op.drop_index("ix_tcc_destinations_un_country_id", table_name="tcc_destinations")
