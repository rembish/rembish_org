"""Add extended reference data to un_countries

Revision ID: 032
Revises: 031
Create Date: 2026-02-16

Adds languages, tipping, speed_limits, visa_free_days, eu_roaming
to un_countries. Seeds data for all 193 UN member states.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "un_countries",
        sa.Column("languages", sa.String(200), nullable=True),
    )
    op.add_column(
        "un_countries",
        sa.Column("tipping", sa.String(200), nullable=True),
    )
    op.add_column(
        "un_countries",
        sa.Column("speed_limits", sa.String(50), nullable=True),
    )
    op.add_column(
        "un_countries",
        sa.Column("visa_free_days", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "un_countries",
        sa.Column("eu_roaming", sa.Boolean(), nullable=True),
    )

    bind = op.get_bind()

    # (iso_alpha2, languages, tipping, speed_limits, visa_free_days, eu_roaming)
    # speed_limits format: "city/rural/highway" in km/h
    # visa_free_days: for Czech passport holders (0 = visa required, -1 = unlimited/EU)
    # tipping: brief guide
    data = [
        ("AF", "Dari, Pashto", "Not expected", "40/60/100", 0, False),
        ("AL", "Albanian", "Round up", "40/80/110", 90, False),
        ("DZ", "Arabic, French", "10%", "40/80/120", 0, False),
        ("AD", "Catalan", "10%", "50/90/110", 90, False),
        ("AO", "Portuguese", "10%", "60/90/120", 0, False),
        ("AG", "English", "10-15%", "30/60/80", 180, False),
        ("AR", "Spanish", "10%", "40/80/130", 90, False),
        ("AM", "Armenian", "10%", "60/90/110", 180, False),
        ("AU", "English", "Not expected", "50/100/110", 90, False),
        ("AT", "German", "5-10%", "50/100/130", -1, True),
        ("AZ", "Azerbaijani", "10%", "40/70/110", 30, False),
        ("BS", "English", "15%", "40/65/80", 90, False),
        ("BH", "Arabic", "10%", "50/80/120", 0, False),
        ("BD", "Bengali", "Not expected", "30/50/80", 0, False),
        ("BB", "English", "10-15%", "40/60/80", 90, False),
        ("BY", "Belarusian, Russian", "10%", "60/90/120", 30, False),
        ("BE", "Dutch, French, German", "Included", "50/90/120", -1, True),
        ("BZ", "English", "10-15%", "40/65/90", 30, False),
        ("BJ", "French", "10%", "50/90/110", 0, False),
        ("BT", "Dzongkha", "Included", "30/40/50", 0, False),
        ("BO", "Spanish, Quechua, Aymara", "10%", "40/80/90", 90, False),
        ("BA", "Bosnian, Croatian, Serbian", "Round up", "50/80/130", 90, False),
        ("BW", "English, Tswana", "10%", "60/100/120", 90, False),
        ("BR", "Portuguese", "10% included", "40/80/110", 90, False),
        ("BN", "Malay", "Not expected", "50/80/100", 90, False),
        ("BG", "Bulgarian", "Round up", "50/90/140", -1, True),
        ("BF", "French", "10%", "50/90/110", 0, False),
        ("BI", "Kirundi, French", "10%", "50/70/100", 0, False),
        ("CV", "Portuguese, Creole", "10%", "40/60/80", 0, False),
        ("KH", "Khmer", "Not expected", "30/60/100", 30, False),
        ("CM", "French, English", "10%", "60/80/110", 0, False),
        ("CA", "English, French", "15-20%", "50/80/100", 180, False),
        ("CF", "French, Sango", "10%", "60/80/100", 0, False),
        ("TD", "French, Arabic", "10%", "60/90/110", 0, False),
        ("CL", "Spanish", "10%", "50/100/120", 90, False),
        ("CN", "Mandarin", "Not expected", "40/70/120", 0, False),
        ("CO", "Spanish", "10%", "30/80/120", 90, False),
        ("KM", "Comorian, French, Arabic", "10%", "40/60/80", 0, False),
        ("CG", "French", "10%", "60/80/110", 0, False),
        ("CD", "French", "10%", "60/80/100", 0, False),
        ("CR", "Spanish", "10% included", "40/60/100", 90, False),
        ("CI", "French", "10%", "50/90/110", 0, False),
        ("HR", "Croatian", "Round up", "50/90/130", -1, True),
        ("CU", "Spanish", "10-15%", "50/60/100", 90, False),
        ("CY", "Greek, Turkish", "10%", "50/80/100", -1, True),
        ("CZ", "Czech", "10%", "50/90/130", -1, True),
        ("DK", "Danish", "Included", "50/80/130", -1, True),
        ("DJ", "French, Arabic", "10%", "40/60/100", 0, False),
        ("DM", "English", "10%", "30/50/80", 21, False),
        ("DO", "Spanish", "10-15%", "40/80/120", 30, False),
        ("EC", "Spanish", "10%", "50/90/120", 90, False),
        ("EG", "Arabic", "10%", "50/90/120", 0, False),
        ("SV", "Spanish", "10%", "40/60/90", 90, False),
        ("GQ", "Spanish, French", "10%", "40/80/100", 0, False),
        ("ER", "Tigrinya, Arabic", "10%", "40/60/100", 0, False),
        ("EE", "Estonian", "10%", "50/90/110", -1, True),
        ("SZ", "English, Swazi", "10%", "60/80/100", 30, False),
        ("ET", "Amharic", "10%", "30/70/100", 0, False),
        ("FJ", "English, Fijian", "Not expected", "50/80/80", 120, False),
        ("FI", "Finnish, Swedish", "Included", "50/80/120", -1, True),
        ("FR", "French", "Included", "50/80/130", -1, True),
        ("GA", "French", "10%", "60/80/120", 0, False),
        ("GM", "English", "Not expected", "50/70/100", 90, False),
        ("GE", "Georgian", "10%", "60/80/110", 365, False),
        ("DE", "German", "5-10%", "50/100/none", -1, True),
        ("GH", "English", "10%", "50/80/100", 0, False),
        ("GR", "Greek", "5-10%", "50/90/130", -1, True),
        ("GD", "English", "10-15%", "30/60/80", 90, False),
        ("GT", "Spanish", "10%", "30/60/100", 90, False),
        ("GN", "French", "Not expected", "50/80/100", 0, False),
        ("GW", "Portuguese", "Not expected", "50/80/100", 0, False),
        ("GY", "English", "10-15%", "30/50/80", 0, False),
        ("HT", "French, Creole", "10%", "40/60/80", 90, False),
        ("HN", "Spanish", "10%", "40/80/100", 90, False),
        ("HU", "Hungarian", "10%", "50/90/130", -1, True),
        ("IS", "Icelandic", "Included", "50/80/90", -1, True),
        ("IN", "Hindi, English", "10%", "50/70/100", 0, False),
        ("ID", "Indonesian", "10%", "50/80/100", 30, False),
        ("IR", "Persian", "10%", "30/85/120", 0, False),
        ("IQ", "Arabic, Kurdish", "10%", "50/80/120", 0, False),
        ("IE", "English, Irish", "10%", "50/80/120", -1, True),
        ("IL", "Hebrew, Arabic", "10-15%", "50/80/110", 90, False),
        ("IT", "Italian", "Round up", "50/90/130", -1, True),
        ("JM", "English", "10-15%", "50/80/110", 30, False),
        ("JP", "Japanese", "Not expected", "40/60/100", 90, False),
        ("JO", "Arabic", "10%", "40/80/110", 0, False),
        ("KZ", "Kazakh, Russian", "10%", "60/90/110", 30, False),
        ("KE", "English, Swahili", "10%", "50/80/110", 0, False),
        ("KI", "English, Gilbertese", "Not expected", "40/60/80", 30, False),
        ("KP", "Korean", "Not expected", "40/60/80", 0, False),
        ("KR", "Korean", "Not expected", "60/80/110", 90, False),
        ("KW", "Arabic", "10%", "45/80/120", 0, False),
        ("KG", "Kyrgyz, Russian", "10%", "60/90/110", 60, False),
        ("LA", "Lao", "Not expected", "30/70/100", 30, False),
        ("LV", "Latvian", "10%", "50/90/110", -1, True),
        ("LB", "Arabic", "15%", "50/80/100", 0, False),
        ("LS", "Sesotho, English", "10%", "50/80/100", 0, False),
        ("LR", "English", "10%", "40/60/80", 0, False),
        ("LY", "Arabic", "Not expected", "50/85/100", 0, False),
        ("LI", "German", "5-10%", "50/80/120", 90, True),
        ("LT", "Lithuanian", "10%", "50/90/130", -1, True),
        ("LU", "French, German, Luxembourgish", "Included", "50/90/130", -1, True),
        ("MG", "Malagasy, French", "10%", "50/80/100", 0, False),
        ("MW", "English, Chichewa", "10%", "50/80/100", 0, False),
        ("MY", "Malay", "Not expected", "50/90/110", 90, False),
        ("MV", "Dhivehi", "10%", "30/50/80", 30, False),
        ("ML", "French", "10%", "50/80/100", 0, False),
        ("MT", "Maltese, English", "10%", "50/80/80", -1, True),
        ("MH", "Marshallese, English", "10%", "40/60/80", 0, False),
        ("MR", "Arabic", "Not expected", "50/80/100", 0, False),
        ("MU", "English, French, Creole", "10%", "40/80/110", 90, False),
        ("MX", "Spanish", "10-15%", "40/80/110", 180, False),
        ("FM", "English", "Not expected", "40/60/80", 30, False),
        ("MD", "Romanian", "10%", "50/90/110", 90, False),
        ("MC", "French", "Included", "50/90/130", 90, False),
        ("MN", "Mongolian", "Round up", "60/80/100", 30, False),
        ("ME", "Montenegrin", "Round up", "50/80/130", 90, False),
        ("MA", "Arabic, Berber, French", "10%", "40/80/120", 90, False),
        ("MZ", "Portuguese", "10%", "60/80/100", 0, False),
        ("MM", "Burmese", "Not expected", "30/60/100", 0, False),
        ("NA", "English", "10%", "60/100/120", 0, False),
        ("NR", "Nauruan, English", "Not expected", "40/60/80", 0, False),
        ("NP", "Nepali", "10%", "30/50/80", 0, False),
        ("NL", "Dutch", "Included", "50/80/130", -1, True),
        ("NZ", "English, Maori", "Not expected", "50/100/100", 90, False),
        ("NI", "Spanish", "10%", "45/80/100", 90, False),
        ("NE", "French", "10%", "50/90/110", 0, False),
        ("NG", "English", "10%", "50/80/100", 0, False),
        ("MK", "Macedonian, Albanian", "Round up", "50/80/130", 90, False),
        ("NO", "Norwegian", "Included", "50/80/110", -1, True),
        ("OM", "Arabic", "Not expected", "40/80/120", 0, False),
        ("PK", "Urdu, English", "10%", "50/80/120", 0, False),
        ("PW", "Palauan, English", "15%", "40/60/80", 30, False),
        ("PA", "Spanish", "10%", "40/80/100", 180, False),
        ("PG", "English, Tok Pisin", "Not expected", "40/60/80", 60, False),
        ("PY", "Spanish, Guarani", "10%", "40/80/110", 90, False),
        ("PE", "Spanish, Quechua", "10%", "35/80/100", 183, False),
        ("PH", "Filipino, English", "10%", "30/60/100", 30, False),
        ("PL", "Polish", "10%", "50/90/140", -1, True),
        ("PT", "Portuguese", "5-10%", "50/90/120", -1, True),
        ("QA", "Arabic", "10%", "50/80/120", 0, False),
        ("RO", "Romanian", "10%", "50/90/130", -1, True),
        ("RU", "Russian", "10%", "60/90/110", 0, False),
        ("RW", "Kinyarwanda, French, English", "10%", "40/60/80", 30, False),
        ("KN", "English", "10-15%", "30/50/80", 90, False),
        ("LC", "English", "10%", "30/50/80", 42, False),
        ("VC", "English", "10%", "30/50/80", 30, False),
        ("WS", "Samoan, English", "Not expected", "40/56/56", 60, False),
        ("SM", "Italian", "Round up", "50/90/130", 90, False),
        ("ST", "Portuguese", "10%", "40/60/80", 15, False),
        ("SA", "Arabic", "Not expected", "50/80/120", 0, False),
        ("SN", "French", "Not expected", "50/80/110", 90, False),
        ("RS", "Serbian", "Round up", "50/80/130", 90, False),
        ("SC", "Creole, English, French", "10%", "40/65/80", 30, False),
        ("SL", "English", "Not expected", "40/60/80", 0, False),
        ("SG", "English, Malay, Mandarin, Tamil", "Not expected", "50/70/90", 90, False),
        ("SK", "Slovak", "10%", "50/90/130", -1, True),
        ("SI", "Slovenian", "10%", "50/90/130", -1, True),
        ("SB", "English", "Not expected", "40/60/80", 90, False),
        ("SO", "Somali, Arabic", "Not expected", "40/60/100", 0, False),
        ("ZA", "English, Zulu, Xhosa + 8", "10-15%", "60/100/120", 30, False),
        ("SS", "English", "Not expected", "40/60/100", 0, False),
        ("ES", "Spanish", "Round up", "50/90/120", -1, True),
        ("LK", "Sinhala, Tamil", "10%", "50/70/100", 0, False),
        ("SD", "Arabic, English", "10%", "50/80/110", 0, False),
        ("SR", "Dutch", "10%", "40/60/80", 90, False),
        ("SE", "Swedish", "Included", "50/90/120", -1, True),
        ("CH", "German, French, Italian", "Included", "50/80/120", 90, True),
        ("SY", "Arabic", "10%", "40/80/110", 0, False),
        ("TJ", "Tajik", "Not expected", "60/90/110", 0, False),
        ("TZ", "Swahili, English", "10%", "50/80/100", 0, False),
        ("TH", "Thai", "Round up", "50/90/120", 60, False),
        ("TL", "Portuguese, Tetum", "10%", "40/60/80", 0, False),
        ("TG", "French", "10%", "40/80/110", 0, False),
        ("TO", "Tongan, English", "Not expected", "40/65/65", 30, False),
        ("TT", "English", "10-15%", "50/80/100", 90, False),
        ("TN", "Arabic, French", "10%", "50/90/110", 90, False),
        ("TR", "Turkish", "10%", "50/90/120", 90, False),
        ("TM", "Turkmen", "Not expected", "60/90/110", 0, False),
        ("TV", "Tuvaluan, English", "Not expected", "40/50/50", 30, False),
        ("UG", "English, Swahili", "10%", "50/80/100", 0, False),
        ("UA", "Ukrainian", "10%", "50/90/130", 90, False),
        ("AE", "Arabic", "10-15%", "40/80/120", 30, False),
        ("GB", "English", "10-15%", "48/96/112", 180, False),
        ("US", "English", "15-20%", "40/89/105", 90, False),
        ("UY", "Spanish", "10%", "45/90/110", 90, False),
        ("UZ", "Uzbek", "10%", "70/100/110", 30, False),
        ("VU", "Bislama, English, French", "Not expected", "50/80/80", 30, False),
        ("VE", "Spanish", "10%", "40/80/120", 90, False),
        ("VN", "Vietnamese", "Round up", "50/80/120", 45, False),
        ("YE", "Arabic", "10%", "40/80/100", 0, False),
        ("ZM", "English", "10%", "50/80/100", 90, False),
        ("ZW", "English, Shona, Ndebele", "10%", "60/80/120", 0, False),
    ]

    for iso, languages, tipping, speed_limits, visa_days, eu_roam in data:
        bind.execute(
            sa.text(
                "UPDATE un_countries SET "
                "languages = :languages, "
                "tipping = :tipping, "
                "speed_limits = :speed_limits, "
                "visa_free_days = :visa_days, "
                "eu_roaming = :eu_roam "
                "WHERE iso_alpha2 = :iso"
            ),
            {
                "languages": languages,
                "tipping": tipping,
                "speed_limits": speed_limits,
                "visa_days": visa_days if visa_days != -1 else None,
                "eu_roam": eu_roam,
                "iso": iso,
            },
        )

    # EU/EEA countries get unlimited stay — mark with NULL visa_free_days
    # but eu_roaming = True (already set above for EU members)
    # For EU countries, visa_free_days=NULL means unlimited


def downgrade() -> None:
    op.drop_column("un_countries", "eu_roaming")
    op.drop_column("un_countries", "visa_free_days")
    op.drop_column("un_countries", "speed_limits")
    op.drop_column("un_countries", "tipping")
    op.drop_column("un_countries", "languages")
