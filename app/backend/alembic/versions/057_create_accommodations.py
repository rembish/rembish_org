"""Create accommodations table

Revision ID: 057
Revises: 056
Create Date: 2026-02-21

Stores accommodation bookings (hotels, apartments) linked to trips,
with encrypted confirmation codes and optional document attachment.
"""

import sqlalchemy as sa
from alembic import op

revision = "057"
down_revision = "056"


def upgrade() -> None:
    op.create_table(
        "accommodations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("property_name", sa.String(200), nullable=False),
        sa.Column("platform", sa.String(20), nullable=True),
        sa.Column("checkin_date", sa.String(10), nullable=True),
        sa.Column("checkout_date", sa.String(10), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("total_amount", sa.String(50), nullable=True),
        sa.Column("payment_status", sa.String(20), nullable=True),
        sa.Column("payment_date", sa.String(10), nullable=True),
        sa.Column("guests", sa.Integer, nullable=True),
        sa.Column("rooms", sa.Integer, nullable=True),
        sa.Column("confirmation_code_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("confirmation_code_masked", sa.String(100), nullable=True),
        sa.Column("booking_url", sa.String(1000), nullable=True),
        sa.Column("document_path", sa.String(500), nullable=True),
        sa.Column("document_name", sa.String(200), nullable=True),
        sa.Column("document_mime_type", sa.String(100), nullable=True),
        sa.Column("document_size", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("accommodations")
