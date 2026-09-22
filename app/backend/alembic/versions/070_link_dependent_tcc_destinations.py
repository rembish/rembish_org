"""Link dependent TCC destinations to their sovereign UN country.

The trip Info tab builds each card from the UN country behind a TCC destination,
so a destination with no un_country_id renders an empty card. Dependencies were
meant to be linked all along — Greenland points at Denmark, the Canary Islands at
Spain — but 107 of 330 rows were left NULL, so territories such as the Faroe
Islands and Ceuta/Melilla showed nothing at all.

Sovereigns come from the "sovereign" property of the tcc-topojson package
(rembish/tcc-topojson 1.1.0), matched by name. Ceuta/Melilla and the Bismarck
Archipelago are absent from that dataset and are mapped by hand.

Deliberately still NULL, because they have no UN member behind them: Kosovo,
Palestine, Taiwan, Vatican City, Cook Islands, Niue, Abkhazia, South Ossetia,
Transnistria and Kashmir; the seven Antarctic territories, where inheriting the
claimant's sockets and currency would be meaningless; and Hong Kong, Macau,
Hainan and Tibet, pending territory-level data — Hong Kong and Macau genuinely
differ from mainland China on driving side, currency and plug type.

Matching is by name rather than id so the result does not depend on row ids, and
only rows that are still NULL are touched.
"""

import sqlalchemy as sa

from alembic import op

revision = "070"
down_revision = "069"

# (TCC destination name, UN country name)
LINKS: list[tuple[str, str]] = [
    ("Alaska", "United States"),
    ("American Samoa", "United States"),
    ("Andaman-Nicobar Islands", "India"),
    ("Anguilla", "United Kingdom"),
    ("Aruba", "Netherlands"),
    ("Ascension", "United Kingdom"),
    ("Austral Islands", "France"),
    ("Azores Islands", "Portugal"),
    ("Bahamas", "Bahamas"),
    ("Bermuda", "United Kingdom"),
    ("Bismarck Archipelago", "Papua New Guinea"),
    ("Bonaire", "Netherlands"),
    ("British Indian Ocean Territory", "United Kingdom"),
    ("British Virgin Islands", "United Kingdom"),
    ("Cabinda", "Angola"),
    ("Cayman Islands", "United Kingdom"),
    ("Ceuta, Melilla", "Spain"),
    ("Chatham Islands", "New Zealand"),
    ("Christmas Island", "Australia"),
    ("Cocos (Keeling) Islands", "Australia"),
    ("Curacao", "Netherlands"),
    ("Easter Island", "Chile"),
    ("Egypt, Sinai", "Egypt"),
    ("Equatorial Guinea, Bioko", "Equatorial Guinea"),
    ("Equatorial Guinea, Rio Muni", "Equatorial Guinea"),
    ("Falkland Islands", "United Kingdom"),
    ("Faroe Islands", "Denmark"),
    ("Fernando de Noronha", "Brazil"),
    ("French Guiana", "France"),
    ("French Polynesia", "France"),
    ("Galapagos Islands", "Ecuador"),
    ("Grenada", "Grenada"),
    ("Guadeloupe", "France"),
    ("Guam", "United States"),
    ("Hawaiian Islands", "United States"),
    ("Indonesia, Java", "Indonesia"),
    ("Indonesia, Kalimantan", "Indonesia"),
    ("Indonesia, Papua", "Indonesia"),
    ("Indonesia, Sulawesi", "Indonesia"),
    ("Indonesia, Sumatra", "Indonesia"),
    ("Juan Fernandez Islands", "Chile"),
    ("Kaliningrad", "Russia"),
    ("Lakshadweep", "India"),
    ("Lampedusa", "Italy"),
    ("Lesser Sunda Islands", "Indonesia"),
    ("Lord Howe Island", "Australia"),
    ("Maluku Islands", "Indonesia"),
    ("Marquesas Islands", "France"),
    ("Martinique", "France"),
    ("Mayotte", "France"),
    ("Midway Island", "United States"),
    ("Montserrat", "United Kingdom"),
    ("Nakhchivan", "Azerbaijan"),
    ("Nevis", "Saint Kitts and Nevis"),
    ("New Caledonia", "France"),
    ("Norfolk Island", "Australia"),
    ("Northern Marianas", "United States"),
    ("Nueva Esparta", "Venezuela"),
    ("Ogasawara", "Japan"),
    ("Phoenix Islands", "Kiribati"),
    ("Pitcairn Island", "United Kingdom"),
    ("Prince Edward Island", "Canada"),
    ("Puerto Rico", "United States"),
    ("Reunion", "France"),
    ("Rodrigues Island", "Mauritius"),
    ("Ryukyu Islands", "Japan"),
    ("Saba and Sint Eustatius", "Netherlands"),
    ("Sabah", "Malaysia"),
    ("San Andres & Providencia", "Colombia"),
    ("Sarawak", "Malaysia"),
    ("Sikkim", "India"),
    ("Sint Maarten", "Netherlands"),
    ("South Georgia", "United Kingdom"),
    ("St. Barthélemy", "France"),
    ("St. Helena", "United Kingdom"),
    ("St. Martin", "France"),
    ("St. Pierre and Miquelon", "France"),
    ("Tasmania", "Australia"),
    ("Tokelau Islands", "New Zealand"),
    ("Tristan da Cunha", "United Kingdom"),
    ("Turks and Caicos Islands", "United Kingdom"),
    ("U.S. Virgin Islands", "United States"),
    ("Wake Island", "United States"),
    ("Wallis and Futuna Islands", "France"),
    ("Zanzibar", "Tanzania"),
    ("Zil Elwannyen Sesel", "Seychelles"),
]


def upgrade() -> None:
    conn = op.get_bind()
    stmt = sa.text(
        "UPDATE tcc_destinations SET un_country_id = ("
        "  SELECT id FROM un_countries WHERE name = :un_name"
        ") WHERE name = :dest_name AND un_country_id IS NULL"
    )
    for dest_name, un_name in LINKS:
        conn.execute(stmt, {"un_name": un_name, "dest_name": dest_name})


def downgrade() -> None:
    conn = op.get_bind()
    stmt = sa.text(
        "UPDATE tcc_destinations SET un_country_id = NULL "
        "WHERE name = :dest_name AND un_country_id = ("
        "  SELECT id FROM un_countries WHERE name = :un_name"
        ")"
    )
    for dest_name, un_name in LINKS:
        conn.execute(stmt, {"un_name": un_name, "dest_name": dest_name})
