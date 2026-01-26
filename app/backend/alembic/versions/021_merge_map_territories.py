"""Merge territories into parent countries in the map.

These territories are now merged in the TopoJSON map file:
- Western Sahara -> Morocco
- Somaliland -> Somalia
- Northern Cyprus -> Cyprus

We update map_region_codes and clear TCC map_region_code for Somaliland
so visits use the parent country's region code.

Revision ID: 021
Revises: 020
Create Date: 2025-01-26
"""

from alembic import op
from sqlalchemy import text

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update Morocco: remove Western Sahara code (732)
    op.execute(
        text(
            "UPDATE un_countries SET map_region_codes = '504' "
            "WHERE iso_alpha2 = 'MA'"
        )
    )

    # Update Somalia: remove Somaliland code (-3)
    op.execute(
        text(
            "UPDATE un_countries SET map_region_codes = '706' "
            "WHERE iso_alpha2 = 'SO'"
        )
    )

    # Link Somaliland to Somalia and clear its map_region_code
    # TCC index 231 = Somaliland, Somalia iso_alpha2 = SO
    op.execute(
        text(
            "UPDATE tcc_destinations SET "
            "map_region_code = NULL, "
            "un_country_id = (SELECT id FROM un_countries WHERE iso_alpha2 = 'SO') "
            "WHERE tcc_index = 231"
        )
    )


def downgrade() -> None:
    # Restore Morocco with Western Sahara code
    op.execute(
        text(
            "UPDATE un_countries SET map_region_codes = '504,732' "
            "WHERE iso_alpha2 = 'MA'"
        )
    )

    # Restore Somalia with Somaliland code
    op.execute(
        text(
            "UPDATE un_countries SET map_region_codes = '706,-3' "
            "WHERE iso_alpha2 = 'SO'"
        )
    )

    # Restore Somaliland as de facto state (no UN link, own map code)
    op.execute(
        text(
            "UPDATE tcc_destinations SET "
            "map_region_code = '-3', "
            "un_country_id = NULL "
            "WHERE tcc_index = 231"
        )
    )
