"""Seed per-territory country-info overrides, and link the China SARs.

Values come from ../tripclimate_com/data/ (sockets.json, driving.json,
tap_water.json, timezones.json), captured 2026-09-22. Each territory is compared
against what its sovereign row in un_countries actually holds, so a value appears
here only when the Info tab would otherwise show something different from reality.

Deliberately not imported:
  - speed_limits: tripclimate carries the same 50/90/120 placeholder for 197 of its
    249 entries and for every territory, so importing it would replace real
    sovereign values (France 50/80/130) with a default.
  - tipping: un_countries holds hand-written prose while tripclimate holds an enum;
    the differences are formatting, not substance.
  - currency: tripclimate has no source for it (payments.json covers 61 countries,
    none of these), so territories with their own currency such as Aruba, the
    Cayman Islands and Hong Kong still show their sovereign's. Tracked in ops TODO.

Hong Kong, Macau, Hainan and Tibet are linked to China here rather than in 070,
because linking them was only safe once overrides existed: Hong Kong and Macau
drive on the left and use Type D/G sockets, neither of which is true of mainland
China. Hainan and Tibet are ordinary provinces and inherit everything.
"""

import sqlalchemy as sa

from alembic import op

revision = "072"
down_revision = "071"

# TCC destination name -> the fields that differ from its sovereign
OVERRIDES: dict[str, dict[str, object]] = {
    "Aland Islands": {"timezone": "Europe/Mariehamn", "lat": 60.1, "lng": 19.94},
    "American Samoa": {
        "socket_types": "A,B,F,I",
        "tap_water": "generally_safe",
        "timezone": "Pacific/Pago_Pago",
        "lat": -14.27,
        "lng": -170.7,
    },
    "Anguilla": {
        "socket_types": "A",
        "voltage": "110V 60Hz",
        "tap_water": "generally_safe",
        "timezone": "America/Anguilla",
        "lat": 18.22,
        "lng": -63.06,
    },
    "Aruba": {
        "socket_types": "A,B,F",
        "voltage": "127V 60Hz",
        "timezone": "America/Aruba",
        "lat": 12.51,
        "lng": -70.03,
    },
    "Bermuda": {
        "socket_types": "A,B",
        "voltage": "120V 60Hz",
        "timezone": "Atlantic/Bermuda",
        "lat": 32.29,
        "lng": -64.78,
    },
    "Bonaire": {"timezone": "America/Kralendijk", "lat": 12.14, "lng": -68.27},
    "British Indian Ocean Territory": {
        "driving_side": "right",
        "timezone": "Indian/Chagos",
        "lat": -7.3,
        "lng": 72.4,
    },
    "British Virgin Islands": {
        "socket_types": "A,B",
        "voltage": "110V 60Hz",
        "tap_water": "generally_safe",
        "timezone": "America/Tortola",
        "lat": 18.43,
        "lng": -64.62,
    },
    "Cayman Islands": {
        "socket_types": "A,B",
        "voltage": "120V 60Hz",
        "timezone": "America/Cayman",
        "lat": 19.29,
        "lng": -81.38,
    },
    "Christmas Island": {"timezone": "Indian/Christmas", "lat": -10.42, "lng": 105.68},
    "Cocos (Keeling) Islands": {"timezone": "Indian/Cocos", "lat": -12.19, "lng": 96.83},
    "Curacao": {
        "socket_types": "A,B,C,F",
        "voltage": "127V 50Hz",
        "timezone": "America/Curacao",
        "lat": 12.11,
        "lng": -68.94,
    },
    "Falkland Islands": {
        "voltage": "240V 50Hz",
        "timezone": "Atlantic/Stanley",
        "lat": -51.7,
        "lng": -57.85,
    },
    "Faroe Islands": {"timezone": "Atlantic/Faroe", "lat": 62.01, "lng": -6.77},
    "French Guiana": {
        "socket_types": "C,D,E",
        "voltage": "220V 50Hz",
        "tap_water": "generally_safe",
        "timezone": "America/Cayenne",
        "lat": 4.94,
        "lng": -52.33,
    },
    "French Polynesia": {
        "tap_water": "generally_safe",
        "timezone": "Pacific/Tahiti",
        "lat": -17.54,
        "lng": -149.57,
    },
    "Gibraltar": {
        "socket_types": "C,G",
        "voltage": "240V 50Hz",
        "driving_side": "right",
        "timezone": "Europe/Gibraltar",
        "lat": 36.14,
        "lng": -5.35,
    },
    "Greenland": {"timezone": "America/Nuuk", "lat": 64.18, "lng": -51.72},
    "Guadeloupe": {
        "socket_types": "C,D,E",
        "timezone": "America/Guadeloupe",
        "lat": 16.0,
        "lng": -61.73,
    },
    "Guam": {"voltage": "110V 60Hz", "timezone": "Pacific/Guam", "lat": 13.47, "lng": 144.75},
    "Guernsey": {"timezone": "Europe/Guernsey", "lat": 49.45, "lng": -2.54},
    "Hong Kong": {
        "socket_types": "D,G",
        "driving_side": "left",
        "tap_water": "safe",
        "timezone": "Asia/Hong_Kong",
        "lat": 22.28,
        "lng": 114.16,
    },
    "Isle of Man": {
        "socket_types": "C,G",
        "voltage": "240V 50Hz",
        "timezone": "Europe/Isle_of_Man",
        "lat": 54.15,
        "lng": -4.48,
    },
    "Jersey": {"timezone": "Europe/Jersey", "lat": 49.19, "lng": -2.11},
    "Macau": {
        "socket_types": "D,F,G,M",
        "driving_side": "left",
        "tap_water": "safe",
        "timezone": "Asia/Macau",
        "lat": 22.2,
        "lng": 113.54,
    },
    "Martinique": {
        "socket_types": "C,D,E",
        "voltage": "220V 50Hz",
        "timezone": "America/Martinique",
        "lat": 14.6,
        "lng": -61.08,
    },
    "Mayotte": {"tap_water": "caution", "timezone": "Indian/Mayotte", "lat": -12.78, "lng": 45.23},
    "Montserrat": {
        "socket_types": "A,B",
        "voltage": "230V 60Hz",
        "tap_water": "generally_safe",
        "timezone": "America/Montserrat",
        "lat": 16.71,
        "lng": -62.22,
    },
    "New Caledonia": {
        "socket_types": "C,F",
        "voltage": "220V 50Hz",
        "timezone": "Pacific/Noumea",
        "lat": -22.28,
        "lng": 166.46,
    },
    "Norfolk Island": {"timezone": "Pacific/Norfolk", "lat": -29.06, "lng": 167.96},
    "Northern Marianas": {
        "tap_water": "generally_safe",
        "timezone": "Pacific/Saipan",
        "lat": 15.21,
        "lng": 145.75,
    },
    "Pitcairn Island": {
        "tap_water": "generally_safe",
        "timezone": "Pacific/Pitcairn",
        "lat": -25.07,
        "lng": -130.1,
    },
    "Puerto Rico": {"timezone": "America/Puerto_Rico", "lat": 18.47, "lng": -66.12},
    "Reunion": {
        "socket_types": "E",
        "voltage": "220V 50Hz",
        "timezone": "Indian/Reunion",
        "lat": -20.88,
        "lng": 55.45,
    },
    "Saba and Sint Eustatius": {"timezone": "America/Kralendijk", "lat": 12.14, "lng": -68.27},
    "Sint Maarten": {"timezone": "America/Lower_Princes", "lat": 18.04, "lng": -63.05},
    "South Georgia": {
        "driving_side": "right",
        "timezone": "Atlantic/South_Georgia",
        "lat": -54.28,
        "lng": -36.51,
    },
    "St. Barthélemy": {"timezone": "America/St_Barthelemy", "lat": 17.9, "lng": -62.85},
    "St. Helena": {
        "tap_water": "generally_safe",
        "timezone": "Atlantic/St_Helena",
        "lat": -15.93,
        "lng": -5.72,
    },
    "St. Martin": {
        "socket_types": "C,F",
        "voltage": "120V 60Hz",
        "timezone": "America/Marigot",
        "lat": 18.07,
        "lng": -63.08,
    },
    "St. Pierre and Miquelon": {"timezone": "America/Miquelon", "lat": 46.78, "lng": -56.18},
    "Tokelau Islands": {
        "tap_water": "caution",
        "timezone": "Pacific/Fakaofo",
        "lat": -9.17,
        "lng": -171.82,
    },
    "Turks and Caicos Islands": {
        "socket_types": "A,B",
        "voltage": "120V 60Hz",
        "tap_water": "unsafe",
        "timezone": "America/Grand_Turk",
        "lat": 21.46,
        "lng": -71.14,
    },
    "U.S. Virgin Islands": {
        "voltage": "110V 60Hz",
        "driving_side": "left",
        "timezone": "America/St_Thomas",
        "lat": 18.34,
        "lng": -64.93,
    },
    "Wallis and Futuna Islands": {
        "tap_water": "caution",
        "timezone": "Pacific/Wallis",
        "lat": -13.28,
        "lng": -176.18,
    },
    "Western Sahara": {
        "tap_water": "unsafe",
        "timezone": "Africa/El_Aaiun",
        "lat": 27.15,
        "lng": -13.2,
    },
}

# Linked here rather than in 070; see the module docstring.
CHINA_LINKS = ("Hong Kong", "Macau", "Hainan Island", "Tibet")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE tcc_destinations SET un_country_id = ("
            "  SELECT id FROM un_countries WHERE name = 'China'"
            ") WHERE name IN :names AND un_country_id IS NULL"
        ).bindparams(sa.bindparam("names", expanding=True)),
        {"names": list(CHINA_LINKS)},
    )
    for dest_name, fields in OVERRIDES.items():
        assignments = ", ".join(f"{col} = :{col}" for col in fields)
        conn.execute(
            sa.text(f"UPDATE tcc_destinations SET {assignments} WHERE name = :dest_name"),
            {**fields, "dest_name": dest_name},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for dest_name, fields in OVERRIDES.items():
        assignments = ", ".join(f"{col} = NULL" for col in fields)
        conn.execute(
            sa.text(f"UPDATE tcc_destinations SET {assignments} WHERE name = :dest_name"),
            {"dest_name": dest_name},
        )
    conn.execute(
        sa.text("UPDATE tcc_destinations SET un_country_id = NULL WHERE name IN :names").bindparams(
            sa.bindparam("names", expanding=True)
        ),
        {"names": list(CHINA_LINKS)},
    )
