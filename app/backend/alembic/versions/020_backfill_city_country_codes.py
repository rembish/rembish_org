"""Backfill country_code for existing cities.

Revision ID: 020
Revises: 019
Create Date: 2025-01-25
"""

from alembic import op
from sqlalchemy import text

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None

# Manual mappings for territories and alternative names
TERRITORY_MAPPINGS = {
    "Abu Dhabi": "AE",
    "Aegean Islands": "GR",
    "Ajman": "AE",
    "Aland Islands": "AX",
    "Azores": "PT",
    "Balearic Islands": "ES",
    "Canary Islands": "ES",
    "Cape Verde Islands": "CV",
    "Corsica": "FR",
    "Crete": "GR",
    "Dubai": "AE",
    "Egypt in Africa": "EG",
    "England": "GB",
    "Faroe Islands": "FO",
    "Fujairah": "AE",
    "Gibraltar": "GI",
    "Greenland": "GL",
    "Guernsey": "GG",
    "Hong Kong": "HK",
    "Ibiza": "ES",
    "Ionian Islands": "GR",
    "Isle of Man": "IM",
    "Jersey": "JE",
    "Kosovo": "XK",
    "Macau": "MO",
    "Madeira": "PT",
    "Mallorca": "ES",
    "Northern Ireland": "GB",
    "Palestine": "PS",
    "Ras al Khaimah": "AE",
    "Sardinia": "IT",
    "Scotland": "GB",
    "Sharjah": "AE",
    "Sicily": "IT",
    "Socotra": "YE",
    "South Korea, Jeju": "KR",
    "Spitsbergen": "SJ",
    "Svalbard": "SJ",
    "Taiwan": "TW",
    "Turkey, Europe": "TR",
    "Umm al Quwain": "AE",
    "Vatican City": "VA",
    "Wales": "GB",
}


def upgrade() -> None:
    conn = op.get_bind()

    # First, update from un_countries table (exact name match)
    conn.execute(text("""
        UPDATE cities c
        JOIN un_countries u ON LOWER(c.country) = LOWER(u.name)
        SET c.country_code = u.iso_alpha2
        WHERE c.country_code IS NULL
    """))

    # Then apply manual mappings for territories
    for country, code in TERRITORY_MAPPINGS.items():
        conn.execute(
            text("""
                UPDATE cities
                SET country_code = :code
                WHERE LOWER(country) = LOWER(:country) AND country_code IS NULL
            """),
            {"code": code, "country": country},
        )

    # Fix missing TCC to UN country mappings
    # Cyprus UK bases and Gibraltar -> United Kingdom
    conn.execute(text("""
        UPDATE tcc_destinations
        SET un_country_id = (SELECT id FROM un_countries WHERE name = 'United Kingdom')
        WHERE id IN (125, 135) AND un_country_id IS NULL
    """))
    # Russia, Asia -> Russia
    conn.execute(text("""
        UPDATE tcc_destinations
        SET un_country_id = (SELECT id FROM un_countries WHERE name = 'Russia')
        WHERE id = 313 AND un_country_id IS NULL
    """))


def downgrade() -> None:
    # Clear all country_codes (will be re-populated on next Nominatim fetch)
    op.execute("UPDATE cities SET country_code = NULL")
