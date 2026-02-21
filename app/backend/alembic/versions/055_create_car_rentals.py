"""Create car_rentals table

Revision ID: 055
Revises: 054
Create Date: 2026-02-21

Stores car rental reservations linked to trips, with encrypted confirmation numbers.
"""

import sqlalchemy as sa
from alembic import op

revision = "055"
down_revision = "054"


def upgrade() -> None:
    op.create_table(
        "car_rentals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("rental_company", sa.String(100), nullable=False),
        sa.Column("car_class", sa.String(100), nullable=True),
        sa.Column("actual_car", sa.String(100), nullable=True),
        sa.Column("transmission", sa.String(10), nullable=True),
        sa.Column("pickup_location", sa.String(200), nullable=True),
        sa.Column("dropoff_location", sa.String(200), nullable=True),
        sa.Column("pickup_datetime", sa.String(20), nullable=True),
        sa.Column("dropoff_datetime", sa.String(20), nullable=True),
        sa.Column("is_paid", sa.Boolean, nullable=True),
        sa.Column("total_amount", sa.String(50), nullable=True),
        sa.Column("confirmation_number_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("confirmation_number_masked", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("car_rentals")
