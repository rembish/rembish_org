"""Add flight_path column to drone_flights

Revision ID: 060
Revises: 059
Create Date: 2026-02-23

Stores simplified flight path as JSON array of [lng, lat] coordinate pairs,
decimated from full DJI telemetry using Ramer-Douglas-Peucker algorithm.
"""

import sqlalchemy as sa
from alembic import op

revision = "060"
down_revision = "059"


def upgrade() -> None:
    op.add_column("drone_flights", sa.Column("flight_path", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("drone_flights", "flight_path")
