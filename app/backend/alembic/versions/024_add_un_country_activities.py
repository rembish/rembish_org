"""Add driving_type and drone_flown columns to un_countries table.

Revision ID: 024
Revises: 023
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "un_countries",
        sa.Column("driving_type", sa.String(10), nullable=True),
    )
    op.add_column(
        "un_countries",
        sa.Column("drone_flown", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("un_countries", "drone_flown")
    op.drop_column("un_countries", "driving_type")
