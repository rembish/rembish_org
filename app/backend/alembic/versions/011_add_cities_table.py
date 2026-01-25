"""Add cities table for geocoding

Revision ID: 011
Revises: 010
Create Date: 2026-01-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create cities reference table
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=True),  # For disambiguation
        sa.Column("display_name", sa.String(500), nullable=True),  # Full name from geocoder
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("geocoded_at", sa.DateTime(), nullable=True),
        sa.Column("confidence", sa.String(20), nullable=True),  # high/medium/low/manual/failed
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cities_name", "cities", ["name"])
    op.create_index("ix_cities_country", "cities", ["country"])

    # Add city_id to trip_cities (nullable for now during migration)
    op.add_column(
        "trip_cities",
        sa.Column("city_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_trip_cities_city_id",
        "trip_cities",
        "cities",
        ["city_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_trip_cities_city_id", "trip_cities", type_="foreignkey")
    op.drop_column("trip_cities", "city_id")
    op.drop_table("cities")
