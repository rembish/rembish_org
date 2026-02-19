"""Create vault tables

Revision ID: 039
Revises: 038
Create Date: 2026-02-18

Encrypted document storage and loyalty program memberships.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "039"
down_revision: Union[str, None] = "038"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vault_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "doc_type",
            sa.Enum("passport", "id_card", "drivers_license", name="doc_type_enum"),
            nullable=False,
        ),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("issuing_country", sa.String(2), nullable=True),
        sa.Column("issue_date", sa.Date, nullable=True),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("number_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("number_masked", sa.String(100), nullable=True),
        sa.Column("notes_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("notes_masked", sa.String(100), nullable=True),
    )

    op.create_table(
        "vault_loyalty_programs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("program_name", sa.String(100), nullable=False),
        sa.Column(
            "alliance",
            sa.Enum("star_alliance", "oneworld", "skyteam", "none", name="alliance_enum"),
            nullable=False,
            server_default="none",
        ),
        sa.Column("tier", sa.String(50), nullable=True),
        sa.Column("membership_number_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("membership_number_masked", sa.String(100), nullable=True),
        sa.Column("notes_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("notes_masked", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("vault_loyalty_programs")
    op.drop_table("vault_documents")
