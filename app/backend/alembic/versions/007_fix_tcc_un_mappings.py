"""Fix TCC to UN country mappings

Revision ID: 007
Revises: 006
Create Date: 2026-01-24

Fixes missing TCC->UN mappings:
- UAE emirates -> United Arab Emirates
- Territories -> parent countries (Canary Islands->Spain, Madeira->Portugal, etc.)
- Somaliland -> Somalia (for UN count purposes)
- Vatican City -> add map_region_code (not a UN member but needs map coloring)
"""

from alembic import op
from sqlalchemy import text


revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


# Additional TCC->UN mappings that were missing
# Format: tcc_index -> UN country name
ADDITIONAL_MAPPINGS = {
    # UAE emirates
    243: "United Arab Emirates",  # Abu Dhabi
    244: "United Arab Emirates",  # Ajman
    246: "United Arab Emirates",  # Dubai
    248: "United Arab Emirates",  # Fujairah
    258: "United Arab Emirates",  # Ras Al Khaimah
    260: "United Arab Emirates",  # Sharjah
    262: "United Arab Emirates",  # Umm Al Qaiwain
    # Spanish territories
    102: "Spain",  # Canary Islands
    117: "Spain",  # Balearic Islands
    # Portuguese territories
    109: "Portugal",  # Madeira
    # French territories
    122: "France",  # Corsica
    # Greek territories
    123: "Greece",  # Crete
    137: "Greece",  # Greek Aegean Islands
    140: "Greece",  # Ionian Islands
    # Italian territories
    165: "Italy",  # Sardinia
    168: "Italy",  # Sicily
    # UK territories
    138: "United Kingdom",  # Guernsey
    143: "United Kingdom",  # Isle of Man
    145: "United Kingdom",  # Jersey
    # Norway territories
    172: "Norway",  # Spitsbergen
    # Denmark territories
    107: "Denmark",  # Greenland
    # Finland territories
    113: "Finland",  # Aland Islands
    # South Korea territories
    294: "South Korea",  # Jeju Island
    # Yemen territories
    277: "Yemen",  # Socotra
    # Somalia parts
    230: "Somalia",  # Somalia (Italian Somaliland) - was missing in original migration
    231: "Somalia",  # Somaliland (British)
    # Bosnia parts
    173: "Bosnia and Herzegovina",  # Srpska
}

# TCC destinations that need map_region_code (non-UN entities with own map polygon)
TCC_MAP_CODES = {
    179: "336",  # Vatican City (ISO numeric code)
}


def upgrade():
    conn = op.get_bind()

    # Get UN country IDs
    result = conn.execute(text("SELECT id, name FROM un_countries"))
    un_ids = {row[1]: row[0] for row in result}

    # Update TCC destinations with missing UN country mappings
    for tcc_idx, un_name in ADDITIONAL_MAPPINGS.items():
        un_id = un_ids.get(un_name)
        if un_id:
            conn.execute(text(
                f"UPDATE tcc_destinations SET un_country_id = {un_id} WHERE tcc_index = {tcc_idx}"
            ))

    # Add map_region_code to TCC destinations that need their own polygon
    for tcc_idx, map_code in TCC_MAP_CODES.items():
        conn.execute(text(
            f"UPDATE tcc_destinations SET map_region_code = '{map_code}' WHERE tcc_index = {tcc_idx}"
        ))


def downgrade():
    conn = op.get_bind()

    # Remove the mappings we added
    for tcc_idx in ADDITIONAL_MAPPINGS.keys():
        conn.execute(text(
            f"UPDATE tcc_destinations SET un_country_id = NULL WHERE tcc_index = {tcc_idx}"
        ))

    # Remove map_region_codes we added
    for tcc_idx in TCC_MAP_CODES.keys():
        conn.execute(text(
            f"UPDATE tcc_destinations SET map_region_code = NULL WHERE tcc_index = {tcc_idx}"
        ))
