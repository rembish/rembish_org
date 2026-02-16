"""Add cover_media_id to instagram_posts for carousel cover selection

Revision ID: 029
Revises: 028
Create Date: 2026-02-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "instagram_posts",
        sa.Column("cover_media_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_instagram_posts_cover_media",
        "instagram_posts",
        "instagram_media",
        ["cover_media_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_instagram_posts_cover_media", "instagram_posts", type_="foreignkey")
    op.drop_column("instagram_posts", "cover_media_id")
