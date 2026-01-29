"""Create Instagram posts and media tables

Revision ID: 026
Revises: 025
Create Date: 2026-01-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Instagram posts table
    op.create_table(
        "instagram_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ig_id", sa.String(50), nullable=False, unique=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("media_type", sa.String(20), nullable=False),  # IMAGE, CAROUSEL_ALBUM, VIDEO
        sa.Column("posted_at", sa.DateTime(), nullable=False),
        sa.Column("permalink", sa.String(255), nullable=False),
        # IG geotag data (if available)
        sa.Column("ig_location_name", sa.String(255), nullable=True),
        sa.Column("ig_location_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("ig_location_lng", sa.Numeric(10, 7), nullable=True),
        # Labels (all nullable - set during labeling)
        sa.Column("un_country_id", sa.Integer(), sa.ForeignKey("un_countries.id"), nullable=True),
        sa.Column("tcc_destination_id", sa.Integer(), sa.ForeignKey("tcc_destinations.id"), nullable=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="SET NULL"), nullable=True),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_aerial", sa.Boolean(), nullable=True),
        # Workflow
        sa.Column("labeled_at", sa.DateTime(), nullable=True),
        sa.Column("skipped", sa.Boolean(), default=False, nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_instagram_posts_posted_at", "instagram_posts", ["posted_at"])
    op.create_index("ix_instagram_posts_labeled_at", "instagram_posts", ["labeled_at"])

    # Instagram media table (for carousel images and single images)
    op.create_table(
        "instagram_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("instagram_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ig_media_id", sa.String(50), nullable=False),
        sa.Column("media_order", sa.Integer(), nullable=False, default=0),
        sa.Column("media_type", sa.String(20), nullable=False),  # IMAGE, VIDEO
        sa.Column("storage_path", sa.String(500), nullable=True),  # Local or GCS path
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_instagram_media_post_id", "instagram_media", ["post_id"])


def downgrade() -> None:
    op.drop_table("instagram_media")
    op.drop_table("instagram_posts")
