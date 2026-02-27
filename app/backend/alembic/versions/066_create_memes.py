"""Create memes table for meme feed ingestion and curation."""

import sqlalchemy as sa
from alembic import op

revision = "066"
down_revision = "065"


def upgrade() -> None:
    op.create_table(
        "memes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="telegram"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("media_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(50), nullable=False),
        sa.Column("width", sa.Integer, nullable=True),
        sa.Column("height", sa.Integer, nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("category", sa.String(30), nullable=True),
        sa.Column("description_en", sa.Text, nullable=True),
        sa.Column("is_site_worthy", sa.Boolean, nullable=True),
        sa.Column("telegram_message_id", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_memes_status", "memes", ["status"])
    op.create_index("ix_memes_category", "memes", ["category"])
    op.create_index("ix_memes_created_at", "memes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_memes_created_at", "memes")
    op.drop_index("ix_memes_category", "memes")
    op.drop_index("ix_memes_status", "memes")
    op.drop_table("memes")
