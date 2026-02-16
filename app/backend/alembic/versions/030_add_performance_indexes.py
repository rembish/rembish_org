"""Add composite index for labeler navigation queries

Revision ID: 030
Revises: 029
Create Date: 2026-02-16

Note: single-column indexes on instagram_posts(trip_id) and
trip_cities(trip_id) already exist as FK indexes created by MySQL.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_instagram_posts_skipped_labeled_at",
        "instagram_posts",
        ["skipped", "labeled_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_instagram_posts_skipped_labeled_at", "instagram_posts")
