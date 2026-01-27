"""Add user_last_locations table for GPS check-in feature.

Revision ID: 023
Revises: 022
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_last_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_last_locations_user_id", "user_last_locations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_last_locations_user_id", table_name="user_last_locations")
    op.drop_table("user_last_locations")
