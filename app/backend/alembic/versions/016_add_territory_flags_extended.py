"""Add flags for overseas territories (British, US, French, Dutch, etc.).

Revision ID: 016
Revises: 015
Create Date: 2025-01-25
"""

from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Territory flags available in flag-icons
    # Format: (TCC destination name, ISO code for flag)
    territory_flags = [
        # British Territories
        ("Anguilla", "ai"),
        ("Bermuda", "bm"),
        ("British Virgin Islands", "vg"),
        ("Cayman Islands", "ky"),
        ("Falkland Islands", "fk"),
        ("Montserrat", "ms"),
        ("Pitcairn Island", "pn"),
        ("South Georgia", "gs"),
        ("St. Helena", "sh"),
        ("Ascension", "sh-ac"),
        ("Tristan da Cunha", "sh-ta"),
        ("Turks and Caicos Islands", "tc"),
        ("British Indian Ocean Territory", "io"),

        # US Territories
        ("Puerto Rico", "pr"),
        ("U.S. Virgin Islands", "vi"),
        ("Guam", "gu"),
        ("Northern Marianas", "mp"),
        ("American Samoa", "as"),

        # French Territories
        ("French Polynesia", "pf"),
        ("New Caledonia", "nc"),
        ("Martinique", "mq"),
        ("Guadeloupe", "gp"),
        ("French Guiana", "gf"),
        ("Reunion", "re"),
        ("Mayotte", "yt"),
        ("St. Martin", "mf"),
        ("St. Pierre and Miquelon", "pm"),
        ("Wallis and Futuna Islands", "wf"),
        ("French Antarctica", "tf"),

        # Dutch Territories
        ("Aruba", "aw"),
        ("Curacao", "cw"),
        ("Sint Maarten", "sx"),
        ("Bonaire", "bq"),
        ("Saba and Sint Eustatius", "bq"),

        # Danish Territories
        ("Faroe Islands", "fo"),

        # Chinese SARs
        ("Hong Kong", "hk"),
        ("Macau", "mo"),

        # Australian Territories
        ("Norfolk Island", "nf"),
        ("Christmas Island", "cx"),
        ("Cocos (Keeling) Islands", "cc"),

        # New Zealand Territories
        ("Tokelau Islands", "tk"),
    ]

    for tcc_name, iso in territory_flags:
        # Escape single quotes for SQL
        name_escaped = tcc_name.replace("'", "''")
        op.execute(
            f"UPDATE tcc_destinations SET iso_alpha2 = '{iso}' WHERE name = '{name_escaped}'"
        )

    # Handle St. Barthélemy with accent
    op.execute(
        "UPDATE tcc_destinations SET iso_alpha2 = 'bl' "
        "WHERE name LIKE 'St. Barth%'"
    )


def downgrade() -> None:
    # Clear all territory flags added in this migration
    territories = [
        "Anguilla", "Bermuda", "British Virgin Islands", "Cayman Islands",
        "Falkland Islands", "Montserrat", "Pitcairn Island", "South Georgia",
        "St. Helena", "Ascension", "Tristan da Cunha", "Turks and Caicos Islands",
        "British Indian Ocean Territory",
        "Puerto Rico", "U.S. Virgin Islands", "Guam", "Northern Marianas",
        "American Samoa",
        "French Polynesia", "New Caledonia", "Martinique", "Guadeloupe",
        "French Guiana", "Reunion", "Mayotte", "St. Martin",
        "St. Pierre and Miquelon", "Wallis and Futuna Islands", "French Antarctica",
        "Aruba", "Curacao", "Sint Maarten", "Bonaire", "Saba and Sint Eustatius",
        "Faroe Islands",
        "Hong Kong", "Macau",
        "Norfolk Island", "Christmas Island", "Cocos (Keeling) Islands",
        "Tokelau Islands",
    ]
    for name in territories:
        name_escaped = name.replace("'", "''")
        op.execute(f"UPDATE tcc_destinations SET iso_alpha2 = NULL WHERE name = '{name_escaped}'")

    # Handle St. Barthélemy
    op.execute("UPDATE tcc_destinations SET iso_alpha2 = NULL WHERE name LIKE 'St. Barth%'")
