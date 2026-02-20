"""Add created_at and updated_at to vault tables

Revision ID: 045
Revises: 044
Create Date: 2026-02-20

Adds audit timestamps to vault_documents, vault_loyalty_programs,
vault_vaccinations, and vault_travel_docs for tracking record history.
"""

import sqlalchemy as sa

from alembic import op

revision = "045"
down_revision = "044"
branch_labels = None
depends_on = None

TABLES = [
    "vault_documents",
    "vault_loyalty_programs",
    "vault_vaccinations",
    "vault_travel_docs",
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        op.add_column(
            table,
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            ),
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")
