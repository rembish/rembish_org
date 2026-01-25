"""Fix TCC destination UN country links and add ISO codes for sub-regions.

Revision ID: 014
Revises: 013
Create Date: 2025-01-25
"""

from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix UN country links (25 countries)
    # Format: UPDATE tcc SET un_country_id = (SELECT id FROM un WHERE name = 'X') WHERE tcc.name = 'Y'

    un_links = [
        # AFRICA
        ("Congo", "Congo"),
        ("DR Congo", "Congo (DRC)"),
        ("Eswatini", "Eswatini"),
        ("Ivory Coast", "Ivory Coast"),
        ("Sao Tome and Principe", "Sao Tome and Principe"),
        # ASIA
        ("Mongolia", "Mongolia"),
        ("Myanmar", "Myanmar"),
        ("North Korea", "North Korea"),
        ("Sri Lanka", "Sri Lanka"),
        # CARIBBEAN
        ("Antigua and Barbuda", "Antigua and Barbuda"),
        ("Grenada", "Grenada"),
        ("St. Lucia", "Saint Lucia"),
        ("St. Vincent and the Grenadines", "Saint Vincent and the Grenadines"),
        ("Trinidad and Tobago", "Trinidad and Tobago"),
        # INDIAN OCEAN
        ("Comoros", "Comoros"),
        ("Mauritius", "Mauritius"),
        # PACIFIC
        ("Fiji Islands", "Fiji"),
        ("Kiribati", "Kiribati"),
        ("Marshall Islands", "Marshall Islands"),
        ("Micronesia", "Micronesia"),
        ("Palau", "Palau"),
        ("Solomon Islands", "Solomon Islands"),
        ("Tonga", "Tonga"),
        ("Tuvalu", "Tuvalu"),
        ("Vanuatu", "Vanuatu"),
    ]

    for tcc_name, un_name in un_links:
        op.execute(f"""
            UPDATE tcc_destinations
            SET un_country_id = (SELECT id FROM un_countries WHERE name = '{un_name}')
            WHERE name = '{tcc_name}'
        """)

    # Add ISO codes for sub-regions (9 territories)
    iso_codes = [
        ("Taiwan", "TW"),
        ("Kaliningrad", "RU"),
        ("Zanzibar", "TZ"),
        ("Nevis", "KN"),
        ("St. Kitts", "KN"),
        ("Nueva Esparta", "VE"),
        ("Cook Islands", "CK"),
        ("Niue", "NU"),
        ("Equatorial Guinea, Bioko", "GQ"),
        # Abkhazia has no standard ISO code, skipping
    ]

    for tcc_name, iso in iso_codes:
        op.execute(f"UPDATE tcc_destinations SET iso_alpha2 = '{iso}' WHERE name = '{tcc_name}'")


def downgrade() -> None:
    # Remove UN country links
    tcc_names = [
        "Congo", "DR Congo", "Eswatini", "Ivory Coast", "Sao Tome and Principe",
        "Mongolia", "Myanmar", "North Korea", "Sri Lanka",
        "Antigua and Barbuda", "Grenada", "St. Lucia", "St. Vincent and the Grenadines",
        "Trinidad and Tobago", "Comoros", "Mauritius", "Fiji Islands", "Kiribati",
        "Marshall Islands", "Micronesia", "Palau", "Solomon Islands", "Tonga",
        "Tuvalu", "Vanuatu",
    ]
    for name in tcc_names:
        op.execute(f"UPDATE tcc_destinations SET un_country_id = NULL WHERE name = '{name}'")

    # Remove ISO codes for sub-regions
    sub_regions = ["Taiwan", "Kaliningrad", "Zanzibar", "Nevis", "St. Kitts",
                   "Nueva Esparta", "Cook Islands", "Niue", "Equatorial Guinea, Bioko"]
    for name in sub_regions:
        op.execute(f"UPDATE tcc_destinations SET iso_alpha2 = NULL WHERE name = '{name}'")
