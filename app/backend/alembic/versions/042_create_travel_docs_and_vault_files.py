"""Create vault_travel_docs, vault_files, trip_travel_docs, trip_passports

Revision ID: 042
Revises: 041
Create Date: 2026-02-19

Adds travel document storage (e-visas, ETAs, etc.), generic file attachments
for all vault entities, and trip-document association tables.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "042"
down_revision: Union[str, None] = "041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vault_travel_docs table
    op.create_table(
        "vault_travel_docs",
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
            sa.Enum(
                "e_visa",
                "eta",
                "esta",
                "etias",
                "loi",
                "entry_permit",
                "travel_insurance",
                "vaccination_cert",
                "other",
                name="travel_doc_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("valid_from", sa.Date, nullable=True),
        sa.Column("valid_until", sa.Date, nullable=True),
        sa.Column(
            "entry_type",
            sa.Enum("single", "double", "multiple", name="entry_type_enum"),
            nullable=True,
        ),
        sa.Column("notes_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("notes_masked", sa.String(100), nullable=True),
    )

    # Create vault_files table (generic file attachments)
    op.create_table(
        "vault_files",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("vault_documents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "vaccination_id",
            sa.Integer,
            sa.ForeignKey("vault_vaccinations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "travel_doc_id",
            sa.Integer,
            sa.ForeignKey("vault_travel_docs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )

    # Create trip_travel_docs junction table
    op.create_table(
        "trip_travel_docs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "travel_doc_id",
            sa.Integer,
            sa.ForeignKey("vault_travel_docs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.UniqueConstraint("trip_id", "travel_doc_id"),
    )

    # Create trip_passports junction table
    op.create_table(
        "trip_passports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "trip_id",
            sa.Integer,
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("vault_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("trip_id", "document_id"),
    )


def downgrade() -> None:
    op.drop_table("trip_passports")
    op.drop_table("trip_travel_docs")
    op.drop_table("vault_files")
    op.drop_table("vault_travel_docs")
    # Drop enum types (MySQL ignores these, PostgreSQL needs them)
    op.execute("DROP TYPE IF EXISTS travel_doc_type_enum")
    op.execute("DROP TYPE IF EXISTS entry_type_enum")
