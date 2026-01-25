"""Add territory-specific flags for UK nations, Greenland, etc.

Revision ID: 015
Revises: 014
Create Date: 2025-01-25
"""

from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Expand iso_alpha2 column to fit codes like "gb-eng"
    op.alter_column(
        "tcc_destinations",
        "iso_alpha2",
        type_=sa.String(10),
        existing_type=sa.String(2),
        existing_nullable=True,
    )

    # Update territories to use their own flags
    territory_flags = [
        ("England", "gb-eng"),
        ("Scotland", "gb-sct"),
        ("Wales", "gb-wls"),
        ("Northern Ireland", "gb-nir"),
        ("Greenland", "gl"),
        ("Aland Islands", "ax"),
        ("Gibraltar", "gi"),
        ("Guernsey", "gg"),
        ("Jersey", "je"),
        ("Isle of Man", "im"),
        ("Canary Islands", "ic"),
    ]

    for tcc_name, iso in territory_flags:
        op.execute(f"UPDATE tcc_destinations SET iso_alpha2 = '{iso}' WHERE name = '{tcc_name}'")


def downgrade() -> None:
    # Revert to parent country flags
    revert = [
        "England", "Scotland", "Wales", "Northern Ireland",
        "Greenland", "Aland Islands", "Gibraltar", "Guernsey",
        "Jersey", "Isle of Man", "Canary Islands",
    ]
    for name in revert:
        op.execute(f"UPDATE tcc_destinations SET iso_alpha2 = NULL WHERE name = '{name}'")

    # Shrink column back
    op.alter_column(
        "tcc_destinations",
        "iso_alpha2",
        type_=sa.String(2),
        existing_type=sa.String(10),
        existing_nullable=True,
    )
