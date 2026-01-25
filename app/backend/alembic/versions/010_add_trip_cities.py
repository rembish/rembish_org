"""Add trip cities table

Revision ID: 010
Revises: 009
Create Date: 2026-01-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add original_name to tcc_destinations (for preserving full names)
    # Column may already exist if added manually
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SHOW COLUMNS FROM tcc_destinations LIKE 'original_name'")
    )
    if not result.fetchone():
        op.add_column(
            "tcc_destinations",
            sa.Column("original_name", sa.String(255), nullable=True),
        )

    # Create trip_cities table
    op.create_table(
        "trip_cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_partial", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_cities_trip_id", "trip_cities", ["trip_id"])


def downgrade() -> None:
    op.drop_table("trip_cities")
    # Drop original_name column if it exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SHOW COLUMNS FROM tcc_destinations LIKE 'original_name'")
    )
    if result.fetchone():
        op.drop_column("tcc_destinations", "original_name")
