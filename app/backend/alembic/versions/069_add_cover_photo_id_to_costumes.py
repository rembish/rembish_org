"""Add cover_photo_id to cosplay_costumes."""

import sqlalchemy as sa
from alembic import op

revision = "069"
down_revision = "068"


def upgrade() -> None:
    op.add_column(
        "cosplay_costumes",
        sa.Column(
            "cover_photo_id",
            sa.Integer,
            sa.ForeignKey("cosplay_photos.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("cosplay_costumes", "cover_photo_id")
