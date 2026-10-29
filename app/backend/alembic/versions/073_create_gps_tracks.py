"""Create gps_tracks and gps_track_legs tables

Revision ID: 073
Revises: 072
Create Date: 2026-10-29

One row per GNSS logger day file (raw CSV kept in private storage) and the
legs derived from it. Automatic processing only produces stop / gap / foot /
vehicle; the specific modes come from the manual analysis upload.
"""

import sqlalchemy as sa
from alembic import op

revision = "073"
down_revision = "072"


def upgrade() -> None:
    op.create_table(
        "gps_tracks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("source_file", sa.String(200), nullable=False),
        sa.Column("started_at", sa.DateTime, nullable=False, unique=True),
        sa.Column("ended_at", sa.DateTime, nullable=False),
        sa.Column("timezone", sa.String(50), nullable=False),
        sa.Column("local_date", sa.Date, nullable=False, index=True),
        sa.Column("raw_path", sa.String(500), nullable=False),
        sa.Column("raw_size", sa.Integer, nullable=False),
        sa.Column("point_count", sa.Integer, nullable=False),
        sa.Column("wake_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("poi_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("distance_km", sa.Float, nullable=False, server_default="0"),
        sa.Column("max_speed_kmh", sa.Float, nullable=False, server_default="0"),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("legs_source", sa.String(10), nullable=False, server_default="auto"),
        sa.Column("processing_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.CheckConstraint(
            "legs_source IN ('auto', 'annotated')", name="ck_gps_tracks_legs_source"
        ),
    )
    op.create_table(
        "gps_track_legs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "track_id",
            sa.Integer,
            sa.ForeignKey("gps_tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("started_at", sa.DateTime, nullable=False),
        sa.Column("ended_at", sa.DateTime, nullable=False),
        sa.Column("distance_km", sa.Float, nullable=False, server_default="0"),
        sa.Column("max_speed_kmh", sa.Float, nullable=False, server_default="0"),
        sa.Column("lat", sa.Float, nullable=False),
        sa.Column("lon", sa.Float, nullable=False),
        sa.Column("lines", sa.JSON, nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("is_hidden", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("track_id", "seq", name="uq_gps_track_legs_track_seq"),
        sa.CheckConstraint(
            "mode IN ('stop', 'gap', 'foot', 'vehicle', 'walk', 'bicycle', 'animal', 'car', "
            "'bus', 'motorbike', 'train', 'tram', 'metro', 'boat', 'ferry', 'plane', "
            "'cable_car')",
            name="ck_gps_track_legs_mode",
        ),
    )


def downgrade() -> None:
    op.drop_table("gps_track_legs")
    op.drop_table("gps_tracks")
