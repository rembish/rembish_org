"""Add iso_alpha2 field to tcc_destinations for non-UN territories.

Revision ID: 013
Revises: 012
Create Date: 2025-01-25
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tcc_destinations", sa.Column("iso_alpha2", sa.String(2), nullable=True))

    # Set ISO codes for non-UN territories
    op.execute("UPDATE tcc_destinations SET iso_alpha2 = 'XK' WHERE name = 'Kosovo'")
    op.execute("UPDATE tcc_destinations SET iso_alpha2 = 'VA' WHERE name = 'Vatican City'")
    op.execute("UPDATE tcc_destinations SET iso_alpha2 = 'EH' WHERE name = 'Western Sahara'")
    op.execute("UPDATE tcc_destinations SET iso_alpha2 = 'PS' WHERE name = 'Palestine'")


def downgrade() -> None:
    op.drop_column("tcc_destinations", "iso_alpha2")
