"""Add is_cover field to instagram_posts

Revision ID: 027
Revises: 026
Create Date: 2026-01-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "instagram_posts",
        sa.Column("is_cover", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("instagram_posts", "is_cover")
