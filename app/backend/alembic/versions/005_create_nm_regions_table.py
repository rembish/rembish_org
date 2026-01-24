"""Create nm_regions table

Revision ID: 005
Revises: 004
Create Date: 2026-01-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nm_regions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("visited", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("first_visited_year", sa.Integer(), nullable=True),
        sa.Column("last_visited_year", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nm_regions_country", "nm_regions", ["country"])


def downgrade() -> None:
    op.drop_index("ix_nm_regions_country", "nm_regions")
    op.drop_table("nm_regions")
