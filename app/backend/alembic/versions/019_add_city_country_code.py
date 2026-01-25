"""Add country_code field to cities for flag display.

Revision ID: 019
Revises: 018
Create Date: 2025-01-25
"""

from alembic import op
import sqlalchemy as sa

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cities", sa.Column("country_code", sa.String(2), nullable=True))


def downgrade() -> None:
    op.drop_column("cities", "country_code")
