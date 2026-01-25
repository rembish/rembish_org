"""Create trips and trip_destinations tables

Revision ID: 008
Revises: 007
Create Date: 2026-01-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("companions", sa.String(500), nullable=True),
        sa.Column("is_work_trip", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("flights_count", sa.Integer(), nullable=True),
        sa.Column("working_days", sa.Integer(), nullable=True),
        sa.Column("rental_car", sa.String(100), nullable=True),
        sa.Column("raw_countries", sa.Text(), nullable=True),
        sa.Column("raw_cities", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trips_start_date", "trips", ["start_date"])

    op.create_table(
        "trip_destinations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("tcc_destination_id", sa.Integer(), nullable=False),
        sa.Column("is_partial", sa.Boolean(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["trip_id"], ["trips.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tcc_destination_id"], ["tcc_destinations.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trip_destinations_trip_id", "trip_destinations", ["trip_id"]
    )
    op.create_index(
        "ix_trip_destinations_tcc_id", "trip_destinations", ["tcc_destination_id"]
    )


def downgrade() -> None:
    op.drop_table("trip_destinations")
    op.drop_table("trips")
