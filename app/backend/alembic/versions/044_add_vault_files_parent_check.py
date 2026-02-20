"""Add CHECK constraint on vault_files to prevent orphan files

Revision ID: 044
Revises: 043
Create Date: 2026-02-20

Ensures at least one parent FK (document_id, vaccination_id, travel_doc_id)
is non-null on every vault_files row.
"""

from alembic import op

revision = "044"
down_revision = "043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE vault_files ADD CONSTRAINT chk_vault_files_parent "
        "CHECK (document_id IS NOT NULL OR vaccination_id IS NOT NULL OR travel_doc_id IS NOT NULL)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE vault_files DROP CONSTRAINT chk_vault_files_parent")
