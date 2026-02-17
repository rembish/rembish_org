"""Create airports and flights tables

Revision ID: 037
Revises: 036
Create Date: 2026-02-17

Airports are upserted from AeroDataBox API as flights are added.
Flights store per-trip flight details with FK to airports.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "037"
down_revision: Union[str, None] = "036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "airports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("iata_code", sa.String(3), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("timezone", sa.String(50), nullable=True),
    )

    op.create_table(
        "flights",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("flight_date", sa.Date, nullable=False),
        sa.Column("flight_number", sa.String(10), nullable=False),
        sa.Column("airline_name", sa.String(100), nullable=True),
        sa.Column(
            "departure_airport_id",
            sa.Integer,
            sa.ForeignKey("airports.id"),
            nullable=False,
        ),
        sa.Column(
            "arrival_airport_id",
            sa.Integer,
            sa.ForeignKey("airports.id"),
            nullable=False,
        ),
        sa.Column("departure_time", sa.String(5), nullable=True),
        sa.Column("arrival_time", sa.String(5), nullable=True),
        sa.Column("terminal", sa.String(10), nullable=True),
        sa.Column("arrival_terminal", sa.String(10), nullable=True),
        sa.Column("gate", sa.String(10), nullable=True),
        sa.Column("aircraft_type", sa.String(50), nullable=True),
        sa.Column("seat", sa.String(10), nullable=True),
        sa.Column("booking_reference", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )

    op.create_index("ix_flights_trip_id", "flights", ["trip_id"])
    op.create_index("ix_flights_flight_date", "flights", ["flight_date"])


def downgrade() -> None:
    op.drop_table("flights")
    op.drop_table("airports")
