"""Create drone_flights table

Revision ID: 059
Revises: 058
Create Date: 2026-02-23

Stores individual drone flight records from DJI Fly app exports.
Trip FK uses SET NULL — drone flights exist independently of trips.
No max_height column (legal risk).
"""

import sqlalchemy as sa
from alembic import op

revision = "059"
down_revision = "058"


def upgrade() -> None:
    op.create_table(
        "drone_flights",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "drone_id",
            sa.Integer,
            sa.ForeignKey("drones.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("flight_date", sa.Date, nullable=False, index=True),
        sa.Column("takeoff_time", sa.DateTime, nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("duration_sec", sa.Float, nullable=True),
        sa.Column("distance_km", sa.Float, nullable=True),
        sa.Column("max_speed_ms", sa.Float, nullable=True),
        sa.Column("photos", sa.Integer, default=0),
        sa.Column("video_sec", sa.Integer, default=0),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("city", sa.String(200), nullable=True),
        sa.Column("is_hidden", sa.Boolean, default=False),
        sa.Column("source_file", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("drone_flights")
