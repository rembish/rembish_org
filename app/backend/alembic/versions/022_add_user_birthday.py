"""Add birthday field to users.

Revision ID: 022
Revises: 021
Create Date: 2025-01-27
"""

from alembic import op
import sqlalchemy as sa

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("birthday", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "birthday")
