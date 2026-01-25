"""Add description field to trips.

Revision ID: 012
Revises: 011
Create Date: 2025-01-25
"""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("trips", "description")
