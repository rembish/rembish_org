"""Add hidden_from_photos to trips.

Revision ID: 028
Revises: 027
Create Date: 2026-01-30
"""

from alembic import op
import sqlalchemy as sa

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column("hidden_from_photos", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("trips", "hidden_from_photos")
