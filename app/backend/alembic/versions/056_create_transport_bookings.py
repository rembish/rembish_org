"""Create transport_bookings table

Revision ID: 056
Revises: 055
Create Date: 2026-02-21

Stores transport bookings (train, bus, ferry) linked to trips,
with encrypted booking references and optional document attachment.
"""

import sqlalchemy as sa
from alembic import op

revision = "056"
down_revision = "055"


def upgrade() -> None:
    op.create_table(
        "transport_bookings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("operator", sa.String(100), nullable=True),
        sa.Column("service_number", sa.String(50), nullable=True),
        sa.Column("departure_station", sa.String(200), nullable=True),
        sa.Column("arrival_station", sa.String(200), nullable=True),
        sa.Column("departure_datetime", sa.String(20), nullable=True),
        sa.Column("arrival_datetime", sa.String(20), nullable=True),
        sa.Column("carriage", sa.String(20), nullable=True),
        sa.Column("seat", sa.String(20), nullable=True),
        sa.Column("booking_reference_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("booking_reference_masked", sa.String(100), nullable=True),
        sa.Column("document_path", sa.String(500), nullable=True),
        sa.Column("document_name", sa.String(200), nullable=True),
        sa.Column("document_mime_type", sa.String(100), nullable=True),
        sa.Column("document_size", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("transport_bookings")
