"""Add document_id to vault_travel_docs

Revision ID: 043
Revises: 042
"""

from alembic import op
import sqlalchemy as sa

revision = "043"
down_revision = "042"


def upgrade() -> None:
    op.add_column(
        "vault_travel_docs",
        sa.Column("document_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_travel_docs_document",
        "vault_travel_docs",
        "vault_documents",
        ["document_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_travel_docs_document", "vault_travel_docs", type_="foreignkey")
    op.drop_column("vault_travel_docs", "document_id")
