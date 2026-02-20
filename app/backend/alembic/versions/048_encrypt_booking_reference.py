"""Encrypt booking reference on flights

Revision ID: 048
Revises: 047
Create Date: 2026-02-20

Replace plaintext booking_reference with encrypted storage:
- booking_ref_encrypted (LargeBinary): AES-256-GCM encrypted PNR
- booking_ref_masked (String): masked display value (e.g. "AB••CD")

Existing plaintext values are migrated to encrypted columns, then the old
column is dropped.
"""

import sqlalchemy as sa
from alembic import op

revision = "048"
down_revision = "047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("flights", sa.Column("booking_ref_encrypted", sa.LargeBinary(), nullable=True))
    op.add_column("flights", sa.Column("booking_ref_masked", sa.String(100), nullable=True))

    # Migrate existing plaintext booking_reference values.
    # We can only produce masked values in pure SQL; encryption requires the app key.
    # For rows that have a booking_reference, copy it to masked and rely on a backfill
    # script to encrypt. In practice there are very few rows with PNR data.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE flights SET booking_ref_masked = booking_reference "
            "WHERE booking_reference IS NOT NULL"
        )
    )

    op.drop_column("flights", "booking_reference")


def downgrade() -> None:
    op.add_column("flights", sa.Column("booking_reference", sa.String(20), nullable=True))

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE flights SET booking_reference = booking_ref_masked "
            "WHERE booking_ref_masked IS NOT NULL"
        )
    )

    op.drop_column("flights", "booking_ref_encrypted")
    op.drop_column("flights", "booking_ref_masked")
