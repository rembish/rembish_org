"""Create vault_vaccinations table + add proper_name and is_archived to vault_documents

Revision ID: 041
Revises: 040
Create Date: 2026-02-19

Adds vaccination record storage (encrypted batch numbers), a proper_name
field for documents (official name as printed on document), and is_archived
for soft-delete (to preserve future trip-passport FK references).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "041"
down_revision: Union[str, None] = "040"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add proper_name and is_archived to vault_documents
    op.add_column(
        "vault_documents",
        sa.Column("proper_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "vault_documents",
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="0"),
    )

    # Create vault_vaccinations table
    op.create_table(
        "vault_vaccinations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("vaccine_name", sa.String(100), nullable=False),
        sa.Column("brand_name", sa.String(100), nullable=True),
        sa.Column("dose_type", sa.String(50), nullable=True),
        sa.Column("date_administered", sa.Date, nullable=True),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("batch_number_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("batch_number_masked", sa.String(100), nullable=True),
        sa.Column("notes_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("notes_masked", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("vault_vaccinations")
    op.drop_column("vault_documents", "is_archived")
    op.drop_column("vault_documents", "proper_name")
