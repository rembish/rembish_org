"""Create trip_documents table for arbitrary file uploads per trip."""

import sqlalchemy as sa
from alembic import op

revision = "065"
down_revision = "064"


def upgrade() -> None:
    op.create_table(
        "trip_documents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trip_id", sa.Integer, sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("document_path", sa.String(500), nullable=False),
        sa.Column("document_name", sa.String(300), nullable=True),
        sa.Column("document_mime_type", sa.String(100), nullable=True),
        sa.Column("document_size", sa.Integer, nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_trip_documents_trip_id", "trip_documents", ["trip_id"])


def downgrade() -> None:
    op.drop_index("ix_trip_documents_trip_id", "trip_documents")
    op.drop_table("trip_documents")
