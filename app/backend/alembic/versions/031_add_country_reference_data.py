"""Add reference data columns to un_countries

Revision ID: 031
Revises: 030
Create Date: 2026-02-16

Adds socket_types, voltage, phone_code, driving_side, emergency_number,
tap_water, currency_code, capital_lat, capital_lng, timezone to un_countries.
Seeds reference data for all 193 UN member states.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("un_countries", sa.Column("socket_types", sa.String(50), nullable=True))
    op.add_column("un_countries", sa.Column("voltage", sa.String(20), nullable=True))
    op.add_column("un_countries", sa.Column("phone_code", sa.String(20), nullable=True))
    op.add_column("un_countries", sa.Column("driving_side", sa.String(5), nullable=True))
    op.add_column("un_countries", sa.Column("emergency_number", sa.String(20), nullable=True))
    op.add_column("un_countries", sa.Column("tap_water", sa.String(20), nullable=True))
    op.add_column("un_countries", sa.Column("currency_code", sa.String(3), nullable=True))
    op.add_column("un_countries", sa.Column("capital_lat", sa.Float, nullable=True))
    op.add_column("un_countries", sa.Column("capital_lng", sa.Float, nullable=True))
    op.add_column("un_countries", sa.Column("timezone", sa.String(50), nullable=True))

    # Seed reference data for all 193 UN member states
    # Data sourced from Wikipedia public tables (power plugs, currencies, capitals, etc.)
    # fmt: off
    countries = [
        # (iso_alpha2, socket_types, voltage, phone_code, driving_side, emergency_number, tap_water, currency_code, capital_lat, capital_lng, timezone)
        ("AF", "C,F", "220V 50Hz", "+93", "right", "119", "unsafe", "AFN", 34.5553, 69.2075, "Asia/Kabul"),
        ("AL", "C,F", "230V 50Hz", "+355", "right", "112", "safe", "ALL", 41.3275, 19.8187, "Europe/Tirane"),
        ("DZ", "C,F", "230V 50Hz", "+213", "right", "14", "caution", "DZD", 36.7538, 3.0588, "Africa/Algiers"),
        ("AD", "C,F", "230V 50Hz", "+376", "right", "112", "safe", "EUR", 42.5063, 1.5218, "Europe/Andorra"),
        ("AO", "C", "220V 50Hz", "+244", "right", "113", "unsafe", "AOA", -8.8390, 13.2894, "Africa/Luanda"),
        ("AG", "A,B", "230V 60Hz", "+1-268", "left", "911", "safe", "XCD", 17.1274, -61.8468, "America/Antigua"),
        ("AR", "C,I", "220V 50Hz", "+54", "right", "911", "safe", "ARS", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
        ("AM", "C,F", "230V 50Hz", "+374", "right", "112", "safe", "AMD", 40.1792, 44.4991, "Asia/Yerevan"),
        ("AU", "I", "230V 50Hz", "+61", "left", "000", "safe", "AUD", -35.2809, 149.1300, "Australia/Sydney"),
        ("AT", "C,F", "230V 50Hz", "+43", "right", "112", "safe", "EUR", 48.2082, 16.3738, "Europe/Vienna"),
        ("AZ", "C,F", "220V 50Hz", "+994", "right", "112", "caution", "AZN", 40.4093, 49.8671, "Asia/Baku"),
        ("BS", "A,B", "120V 60Hz", "+1-242", "left", "919", "safe", "BSD", 25.0343, -77.3963, "America/Nassau"),
        ("BH", "G", "230V 50Hz", "+973", "right", "999", "safe", "BHD", 26.2285, 50.5860, "Asia/Bahrain"),
        ("BD", "C,D,G,K", "220V 50Hz", "+880", "left", "999", "unsafe", "BDT", 23.8103, 90.4125, "Asia/Dhaka"),
        ("BB", "A,B", "115V 50Hz", "+1-246", "left", "211", "safe", "BBD", 13.1132, -59.5988, "America/Barbados"),
        ("BY", "C,F", "220V 50Hz", "+375", "right", "112", "caution", "BYN", 53.9006, 27.5590, "Europe/Minsk"),
        ("BE", "C,E", "230V 50Hz", "+32", "right", "112", "safe", "EUR", 50.8503, 4.3517, "Europe/Brussels"),
        ("BZ", "A,B,G", "110V 60Hz", "+501", "right", "911", "safe", "BZD", 17.2510, -88.7590, "America/Belize"),
        ("BJ", "C,E", "220V 50Hz", "+229", "right", "117", "unsafe", "XOF", 6.4969, 2.6289, "Africa/Porto-Novo"),
        ("BT", "D,F,G", "230V 50Hz", "+975", "left", "113", "caution", "BTN", 27.4728, 89.6390, "Asia/Thimphu"),
        ("BO", "A,C", "230V 50Hz", "+591", "right", "110", "unsafe", "BOB", -16.4897, -68.1193, "America/La_Paz"),
        ("BA", "C,F", "230V 50Hz", "+387", "right", "112", "safe", "BAM", 43.8563, 18.4131, "Europe/Sarajevo"),
        ("BW", "D,G", "230V 50Hz", "+267", "left", "999", "safe", "BWP", -24.6282, 25.9231, "Africa/Gaborone"),
        ("BR", "C,N", "127/220V 60Hz", "+55", "right", "190", "caution", "BRL", -15.8267, -47.9218, "America/Sao_Paulo"),
        ("BN", "G", "240V 50Hz", "+673", "left", "993", "safe", "BND", 4.9031, 114.9398, "Asia/Brunei"),
        ("BG", "C,F", "230V 50Hz", "+359", "right", "112", "safe", "BGN", 42.6977, 23.3219, "Europe/Sofia"),
        ("BF", "C,E", "220V 50Hz", "+226", "right", "17", "unsafe", "XOF", 12.3714, -1.5197, "Africa/Ouagadougou"),
        ("BI", "C,E", "220V 50Hz", "+257", "right", "117", "unsafe", "BIF", -3.3614, 29.3599, "Africa/Bujumbura"),
        ("CV", "C,F", "220V 50Hz", "+238", "right", "132", "caution", "CVE", 14.9331, -23.5133, "Atlantic/Cape_Verde"),
        ("KH", "A,C,G", "230V 50Hz", "+855", "right", "117", "unsafe", "KHR", 11.5564, 104.9282, "Asia/Phnom_Penh"),
        ("CM", "C,E", "220V 50Hz", "+237", "right", "117", "unsafe", "XAF", 3.8480, 11.5021, "Africa/Douala"),
        ("CA", "A,B", "120V 60Hz", "+1", "right", "911", "safe", "CAD", 45.4215, -75.6972, "America/Toronto"),
        ("CF", "C,E", "220V 50Hz", "+236", "right", "117", "unsafe", "XAF", 4.3947, 18.5582, "Africa/Bangui"),
        ("TD", "C,D,E,F", "220V 50Hz", "+235", "right", "17", "unsafe", "XAF", 12.1348, 15.0557, "Africa/Ndjamena"),
        ("CL", "C,L", "220V 50Hz", "+56", "right", "131", "safe", "CLP", -33.4489, -70.6693, "America/Santiago"),
        ("CN", "A,C,I", "220V 50Hz", "+86", "right", "110", "caution", "CNY", 39.9042, 116.4074, "Asia/Shanghai"),
        ("CO", "A,B", "110V 60Hz", "+57", "right", "123", "caution", "COP", 4.7110, -74.0721, "America/Bogota"),
        ("KM", "C,E", "220V 50Hz", "+269", "right", "17", "unsafe", "KMF", -11.7172, 43.2473, "Indian/Comoro"),
        ("CG", "C,E", "230V 50Hz", "+242", "right", "117", "unsafe", "XAF", -4.2634, 15.2429, "Africa/Brazzaville"),
        ("CD", "C,D,E", "220V 50Hz", "+243", "right", "117", "unsafe", "CDF", -4.4419, 15.2663, "Africa/Kinshasa"),
        ("CR", "A,B", "120V 60Hz", "+506", "right", "911", "safe", "CRC", 9.9281, -84.0907, "America/Costa_Rica"),
        ("CI", "C,E", "220V 50Hz", "+225", "right", "110", "unsafe", "XOF", 6.8276, -5.2893, "Africa/Abidjan"),
        ("HR", "C,F", "230V 50Hz", "+385", "right", "112", "safe", "EUR", 45.8150, 15.9819, "Europe/Zagreb"),
        ("CU", "A,B,C,L", "110/220V 60Hz", "+53", "right", "106", "caution", "CUP", 23.1136, -82.3666, "America/Havana"),
        ("CY", "G", "230V 50Hz", "+357", "left", "112", "safe", "EUR", 35.1856, 33.3823, "Asia/Nicosia"),
        ("CZ", "C,E", "230V 50Hz", "+420", "right", "112", "safe", "CZK", 50.0755, 14.4378, "Europe/Prague"),
        ("DK", "C,E,F,K", "230V 50Hz", "+45", "right", "112", "safe", "DKK", 55.6761, 12.5683, "Europe/Copenhagen"),
        ("DJ", "C,E", "220V 50Hz", "+253", "right", "17", "unsafe", "DJF", 11.5880, 43.1456, "Africa/Djibouti"),
        ("DM", "D,G", "230V 50Hz", "+1-767", "left", "999", "safe", "XCD", 15.3010, -61.3870, "America/Dominica"),
        ("DO", "A,B", "120V 60Hz", "+1-809", "right", "911", "caution", "DOP", 18.4861, -69.9312, "America/Santo_Domingo"),
        ("EC", "A,B", "120V 60Hz", "+593", "right", "911", "caution", "USD", -0.1807, -78.4678, "America/Guayaquil"),
        ("EG", "C,F", "220V 50Hz", "+20", "right", "122", "unsafe", "EGP", 30.0444, 31.2357, "Africa/Cairo"),
        ("SV", "A,B", "115V 60Hz", "+503", "right", "911", "caution", "USD", 13.6929, -89.2182, "America/El_Salvador"),
        ("GQ", "C,E", "220V 50Hz", "+240", "right", "114", "unsafe", "XAF", 3.7504, 8.7371, "Africa/Malabo"),
        ("ER", "C,L", "230V 50Hz", "+291", "right", "114", "unsafe", "ERN", 15.3229, 38.9251, "Africa/Asmara"),
        ("EE", "C,F", "230V 50Hz", "+372", "right", "112", "safe", "EUR", 59.4370, 24.7536, "Europe/Tallinn"),
        ("SZ", "M", "230V 50Hz", "+268", "left", "999", "unsafe", "SZL", -26.3054, 31.1367, "Africa/Mbabane"),
        ("ET", "C,E,F,L", "220V 50Hz", "+251", "right", "911", "unsafe", "ETB", 9.0250, 38.7469, "Africa/Addis_Ababa"),
        ("FJ", "I", "240V 50Hz", "+679", "left", "911", "caution", "FJD", -18.1416, 178.4419, "Pacific/Fiji"),
        ("FI", "C,F", "230V 50Hz", "+358", "right", "112", "safe", "EUR", 60.1699, 24.9384, "Europe/Helsinki"),
        ("FR", "C,E", "230V 50Hz", "+33", "right", "112", "safe", "EUR", 48.8566, 2.3522, "Europe/Paris"),
        ("GA", "C", "220V 50Hz", "+241", "right", "1730", "unsafe", "XAF", 0.4162, 9.4673, "Africa/Libreville"),
        ("GM", "G", "230V 50Hz", "+220", "right", "118", "unsafe", "GMD", 13.4549, -16.5790, "Africa/Banjul"),
        ("GE", "C,F", "220V 50Hz", "+995", "right", "112", "safe", "GEL", 41.7151, 44.8271, "Asia/Tbilisi"),
        ("DE", "C,F", "230V 50Hz", "+49", "right", "112", "safe", "EUR", 52.5200, 13.4050, "Europe/Berlin"),
        ("GH", "D,G", "230V 50Hz", "+233", "right", "191", "unsafe", "GHS", 5.6037, -0.1870, "Africa/Accra"),
        ("GR", "C,F", "230V 50Hz", "+30", "right", "112", "safe", "EUR", 37.9838, 23.7275, "Europe/Athens"),
        ("GD", "G", "230V 50Hz", "+1-473", "left", "911", "safe", "XCD", 12.0561, -61.7488, "America/Grenada"),
        ("GT", "A,B", "120V 60Hz", "+502", "right", "110", "caution", "GTQ", 14.6349, -90.5069, "America/Guatemala"),
        ("GN", "C,F,K", "220V 50Hz", "+224", "right", "117", "unsafe", "GNF", 9.6412, -13.5784, "Africa/Conakry"),
        ("GW", "C", "220V 50Hz", "+245", "right", "117", "unsafe", "XOF", 11.8037, -15.1804, "Africa/Bissau"),
        ("GY", "A,B,D,G", "240V 60Hz", "+592", "left", "911", "caution", "GYD", 6.8013, -58.1551, "America/Guyana"),
        ("HT", "A,B", "110V 60Hz", "+509", "right", "114", "unsafe", "HTG", 18.5944, -72.3074, "America/Port-au-Prince"),
        ("HN", "A,B", "120V 60Hz", "+504", "right", "199", "caution", "HNL", 14.0723, -87.1921, "America/Tegucigalpa"),
        ("HU", "C,F", "230V 50Hz", "+36", "right", "112", "safe", "HUF", 47.4979, 19.0402, "Europe/Budapest"),
        ("IS", "C,F", "230V 50Hz", "+354", "right", "112", "safe", "ISK", 64.1466, -21.9426, "Atlantic/Reykjavik"),
        ("IN", "C,D,M", "230V 50Hz", "+91", "left", "112", "caution", "INR", 28.6139, 77.2090, "Asia/Kolkata"),
        ("ID", "C,F", "230V 50Hz", "+62", "left", "112", "caution", "IDR", -6.2088, 106.8456, "Asia/Jakarta"),
        ("IR", "C,F", "220V 50Hz", "+98", "right", "115", "caution", "IRR", 35.6892, 51.3890, "Asia/Tehran"),
        ("IQ", "C,D,G", "230V 50Hz", "+964", "right", "104", "unsafe", "IQD", 33.3152, 44.3661, "Asia/Baghdad"),
        ("IE", "G", "230V 50Hz", "+353", "left", "112", "safe", "EUR", 53.3498, -6.2603, "Europe/Dublin"),
        ("IL", "C,H", "230V 50Hz", "+972", "right", "100", "safe", "ILS", 31.7683, 35.2137, "Asia/Jerusalem"),
        ("IT", "C,F,L", "230V 50Hz", "+39", "right", "112", "safe", "EUR", 41.9028, 12.4964, "Europe/Rome"),
        ("JM", "A,B", "110V 50Hz", "+1-876", "left", "110", "caution", "JMD", 18.1096, -77.2975, "America/Jamaica"),
        ("JP", "A,B", "100V 50/60Hz", "+81", "left", "110", "safe", "JPY", 35.6762, 139.6503, "Asia/Tokyo"),
        ("JO", "B,C,D,F,G,J", "230V 50Hz", "+962", "right", "911", "safe", "JOD", 31.9454, 35.9284, "Asia/Amman"),
        ("KZ", "C,F", "220V 50Hz", "+7", "right", "112", "caution", "KZT", 51.1694, 71.4491, "Asia/Almaty"),
        ("KE", "G", "240V 50Hz", "+254", "left", "999", "caution", "KES", -1.2921, 36.8219, "Africa/Nairobi"),
        ("KI", "I", "240V 50Hz", "+686", "left", "994", "caution", "AUD", 1.3382, 173.0176, "Pacific/Tarawa"),
        ("KP", "A,C", "220V 50Hz", "+850", "right", "119", "unsafe", "KPW", 39.0392, 125.7625, "Asia/Pyongyang"),
        ("KR", "C,F", "220V 60Hz", "+82", "right", "119", "safe", "KRW", 37.5665, 126.9780, "Asia/Seoul"),
        ("KW", "C,G", "240V 50Hz", "+965", "right", "112", "safe", "KWD", 29.3759, 47.9774, "Asia/Kuwait"),
        ("KG", "C,F", "220V 50Hz", "+996", "right", "112", "caution", "KGS", 42.8746, 74.5698, "Asia/Bishkek"),
        ("LA", "A,B,C,E,F", "230V 50Hz", "+856", "right", "1195", "unsafe", "LAK", 17.9757, 102.6331, "Asia/Vientiane"),
        ("LV", "C,F", "230V 50Hz", "+371", "right", "112", "safe", "EUR", 56.9496, 24.1052, "Europe/Riga"),
        ("LB", "A,B,C,D,G", "220V 50Hz", "+961", "right", "112", "caution", "LBP", 33.8938, 35.5018, "Asia/Beirut"),
        ("LS", "M", "220V 50Hz", "+266", "left", "112", "unsafe", "LSL", -29.3142, 27.4833, "Africa/Maseru"),
        ("LR", "A,B", "120V 60Hz", "+231", "right", "911", "unsafe", "LRD", 6.3004, -10.7969, "Africa/Monrovia"),
        ("LY", "C,L", "127/230V 50Hz", "+218", "right", "1515", "caution", "LYD", 32.8872, 13.1913, "Africa/Tripoli"),
        ("LI", "C,J", "230V 50Hz", "+423", "right", "112", "safe", "CHF", 47.1660, 9.5554, "Europe/Vaduz"),
        ("LT", "C,F", "230V 50Hz", "+370", "right", "112", "safe", "EUR", 54.6872, 25.2797, "Europe/Vilnius"),
        ("LU", "C,F", "230V 50Hz", "+352", "right", "112", "safe", "EUR", 49.6116, 6.1300, "Europe/Luxembourg"),
        ("MG", "C,D,E,J,K", "220V 50Hz", "+261", "right", "117", "unsafe", "MGA", -18.8792, 47.5079, "Indian/Antananarivo"),
        ("MW", "G", "230V 50Hz", "+265", "left", "997", "unsafe", "MWK", -13.9626, 33.7741, "Africa/Blantyre"),
        ("MY", "G", "240V 50Hz", "+60", "left", "999", "safe", "MYR", 3.1390, 101.6869, "Asia/Kuala_Lumpur"),
        ("MV", "A,D,G,J,K,L", "230V 50Hz", "+960", "left", "119", "caution", "MVR", 4.1755, 73.5093, "Indian/Maldives"),
        ("ML", "C,E", "220V 50Hz", "+223", "right", "17", "unsafe", "XOF", 12.6392, -8.0029, "Africa/Bamako"),
        ("MT", "G", "230V 50Hz", "+356", "left", "112", "safe", "EUR", 35.8989, 14.5146, "Europe/Malta"),
        ("MH", "A,B", "120V 60Hz", "+692", "right", "911", "caution", "USD", 7.1164, 171.1858, "Pacific/Majuro"),
        ("MR", "C", "220V 50Hz", "+222", "right", "17", "unsafe", "MRU", 18.0735, -15.9582, "Africa/Nouakchott"),
        ("MU", "C,G", "230V 50Hz", "+230", "left", "999", "safe", "MUR", -20.1609, 57.5012, "Indian/Mauritius"),
        ("MX", "A,B", "127V 60Hz", "+52", "right", "911", "caution", "MXN", 19.4326, -99.1332, "America/Mexico_City"),
        ("FM", "A,B", "120V 60Hz", "+691", "right", "911", "caution", "USD", 6.9248, 158.1610, "Pacific/Pohnpei"),
        ("MD", "C,F", "230V 50Hz", "+373", "right", "112", "caution", "MDL", 47.0105, 28.8638, "Europe/Chisinau"),
        ("MC", "C,D,E,F", "230V 50Hz", "+377", "right", "112", "safe", "EUR", 43.7384, 7.4246, "Europe/Monaco"),
        ("MN", "C,E", "230V 50Hz", "+976", "right", "105", "caution", "MNT", 47.8864, 106.9057, "Asia/Ulaanbaatar"),
        ("ME", "C,F", "230V 50Hz", "+382", "right", "112", "safe", "EUR", 42.4304, 19.2594, "Europe/Podgorica"),
        ("MA", "C,E", "220V 50Hz", "+212", "right", "19", "safe", "MAD", 33.9716, -6.8498, "Africa/Casablanca"),
        ("MZ", "C,F,M", "220V 50Hz", "+258", "left", "119", "unsafe", "MZN", -25.9692, 32.5732, "Africa/Maputo"),
        ("MM", "C,D,F,G", "230V 50Hz", "+95", "right", "199", "unsafe", "MMK", 19.7633, 96.0785, "Asia/Yangon"),
        ("NA", "D,M", "220V 50Hz", "+264", "left", "10111", "caution", "NAD", -22.5609, 17.0658, "Africa/Windhoek"),
        ("NR", "I", "240V 50Hz", "+674", "left", "110", "caution", "AUD", -0.5477, 166.9209, "Pacific/Nauru"),
        ("NP", "C,D,M", "230V 50Hz", "+977", "left", "100", "unsafe", "NPR", 27.7172, 85.3240, "Asia/Kathmandu"),
        ("NL", "C,F", "230V 50Hz", "+31", "right", "112", "safe", "EUR", 52.3676, 4.9041, "Europe/Amsterdam"),
        ("NZ", "I", "230V 50Hz", "+64", "left", "111", "safe", "NZD", -41.2865, 174.7762, "Pacific/Auckland"),
        ("NI", "A,B", "120V 60Hz", "+505", "right", "118", "caution", "NIO", 12.1149, -86.2362, "America/Managua"),
        ("NE", "A,B,C,D,E,F", "220V 50Hz", "+227", "right", "17", "unsafe", "XOF", 13.5116, 2.1254, "Africa/Niamey"),
        ("NG", "D,G", "240V 50Hz", "+234", "right", "112", "unsafe", "NGN", 9.0765, 7.3986, "Africa/Lagos"),
        ("MK", "C,F", "230V 50Hz", "+389", "right", "112", "safe", "MKD", 41.9981, 21.4254, "Europe/Skopje"),
        ("NO", "C,F", "230V 50Hz", "+47", "right", "112", "safe", "NOK", 59.9139, 10.7522, "Europe/Oslo"),
        ("OM", "C,G", "240V 50Hz", "+968", "right", "9999", "safe", "OMR", 23.5880, 58.3829, "Asia/Muscat"),
        ("PK", "C,D", "230V 50Hz", "+92", "left", "115", "unsafe", "PKR", 33.6844, 73.0479, "Asia/Karachi"),
        ("PW", "A,B", "120V 60Hz", "+680", "right", "911", "safe", "USD", 7.5150, 134.5825, "Pacific/Palau"),
        ("PA", "A,B", "120V 60Hz", "+507", "right", "911", "safe", "PAB", 8.9824, -79.5199, "America/Panama"),
        ("PG", "I", "240V 50Hz", "+675", "left", "000", "unsafe", "PGK", -6.3149, 143.9555, "Pacific/Port_Moresby"),
        ("PY", "C", "220V 50Hz", "+595", "right", "911", "caution", "PYG", -25.2637, -57.5759, "America/Asuncion"),
        ("PE", "A,B,C", "220V 60Hz", "+51", "right", "105", "caution", "PEN", -12.0464, -77.0428, "America/Lima"),
        ("PH", "A,B,C", "220V 60Hz", "+63", "right", "911", "caution", "PHP", 14.5995, 120.9842, "Asia/Manila"),
        ("PL", "C,E", "230V 50Hz", "+48", "right", "112", "safe", "PLN", 52.2297, 21.0122, "Europe/Warsaw"),
        ("PT", "C,F", "230V 50Hz", "+351", "right", "112", "safe", "EUR", 38.7223, -9.1393, "Europe/Lisbon"),
        ("QA", "D,G", "240V 50Hz", "+974", "right", "999", "safe", "QAR", 25.2854, 51.5310, "Asia/Qatar"),
        ("RO", "C,F", "230V 50Hz", "+40", "right", "112", "safe", "RON", 44.4268, 26.1025, "Europe/Bucharest"),
        ("RU", "C,F", "220V 50Hz", "+7", "right", "112", "caution", "RUB", 55.7558, 37.6173, "Europe/Moscow"),
        ("RW", "C,J", "230V 50Hz", "+250", "right", "112", "unsafe", "RWF", -1.9403, 29.8739, "Africa/Kigali"),
        ("KN", "D,G", "230V 60Hz", "+1-869", "left", "911", "safe", "XCD", 17.3026, -62.7177, "America/St_Kitts"),
        ("LC", "G", "240V 50Hz", "+1-758", "left", "999", "safe", "XCD", 14.0101, -60.9875, "America/St_Lucia"),
        ("VC", "A,C,E,G,I,K", "230V 50Hz", "+1-784", "left", "999", "safe", "XCD", 13.1587, -61.2248, "America/St_Vincent"),
        ("WS", "I", "230V 50Hz", "+685", "left", "994", "caution", "WST", -13.8333, -171.7500, "Pacific/Apia"),
        ("SM", "C,F,L", "230V 50Hz", "+378", "right", "112", "safe", "EUR", 43.9424, 12.4578, "Europe/San_Marino"),
        ("ST", "C,F", "220V 50Hz", "+239", "right", "112", "unsafe", "STN", 0.1864, 6.6131, "Africa/Sao_Tome"),
        ("SA", "A,B,G", "220V 60Hz", "+966", "right", "911", "safe", "SAR", 24.7136, 46.6753, "Asia/Riyadh"),
        ("SN", "C,D,E,K", "230V 50Hz", "+221", "right", "17", "unsafe", "XOF", 14.7167, -17.4677, "Africa/Dakar"),
        ("RS", "C,F", "230V 50Hz", "+381", "right", "112", "safe", "RSD", 44.7866, 20.4489, "Europe/Belgrade"),
        ("SC", "G", "240V 50Hz", "+248", "left", "999", "safe", "SCR", -4.6191, 55.4513, "Indian/Mahe"),
        ("SL", "D,G", "230V 50Hz", "+232", "right", "999", "unsafe", "SLE", 8.4657, -13.2317, "Africa/Freetown"),
        ("SG", "G", "230V 50Hz", "+65", "left", "999", "safe", "SGD", 1.3521, 103.8198, "Asia/Singapore"),
        ("SK", "C,E", "230V 50Hz", "+421", "right", "112", "safe", "EUR", 48.1486, 17.1077, "Europe/Bratislava"),
        ("SI", "C,F", "230V 50Hz", "+386", "right", "112", "safe", "EUR", 46.0569, 14.5058, "Europe/Ljubljana"),
        ("SB", "G,I", "230V 50Hz", "+677", "left", "999", "caution", "SBD", -9.4456, 160.0356, "Pacific/Guadalcanal"),
        ("SO", "C", "220V 50Hz", "+252", "right", "888", "unsafe", "SOS", 2.0469, 45.3182, "Africa/Mogadishu"),
        ("ZA", "C,D,M,N", "230V 50Hz", "+27", "left", "10111", "safe", "ZAR", -25.7479, 28.2293, "Africa/Johannesburg"),
        ("SS", "C,D", "230V 50Hz", "+211", "right", "999", "unsafe", "SSP", 4.8594, 31.5713, "Africa/Juba"),
        ("ES", "C,F", "230V 50Hz", "+34", "right", "112", "safe", "EUR", 40.4168, -3.7038, "Europe/Madrid"),
        ("LK", "D,G,M", "230V 50Hz", "+94", "left", "110", "caution", "LKR", 6.9271, 79.8612, "Asia/Colombo"),
        ("SD", "C,D", "230V 50Hz", "+249", "right", "999", "unsafe", "SDG", 15.5007, 32.5599, "Africa/Khartoum"),
        ("SR", "A,B,C,F", "127V 60Hz", "+597", "left", "115", "caution", "SRD", 5.8520, -55.2038, "America/Paramaribo"),
        ("SE", "C,F", "230V 50Hz", "+46", "right", "112", "safe", "SEK", 59.3293, 18.0686, "Europe/Stockholm"),
        ("CH", "C,J", "230V 50Hz", "+41", "right", "112", "safe", "CHF", 46.9480, 7.4474, "Europe/Zurich"),
        ("SY", "C,E,L", "220V 50Hz", "+963", "right", "110", "unsafe", "SYP", 33.5138, 36.2765, "Asia/Damascus"),
        ("TJ", "C,F", "220V 50Hz", "+992", "right", "112", "unsafe", "TJS", 38.5598, 68.7740, "Asia/Dushanbe"),
        ("TZ", "D,G", "230V 50Hz", "+255", "left", "114", "unsafe", "TZS", -6.7924, 39.2083, "Africa/Dar_es_Salaam"),
        ("TH", "A,B,C,F,O", "220V 50Hz", "+66", "left", "191", "caution", "THB", 13.7563, 100.5018, "Asia/Bangkok"),
        ("TL", "C,E,F,I", "220V 50Hz", "+670", "left", "112", "unsafe", "USD", -8.5569, 125.5603, "Asia/Dili"),
        ("TG", "C", "220V 50Hz", "+228", "right", "117", "unsafe", "XOF", 6.1256, 1.2254, "Africa/Lome"),
        ("TO", "I", "240V 50Hz", "+676", "left", "911", "caution", "TOP", -21.2133, -175.2018, "Pacific/Tongatapu"),
        ("TT", "A,B", "115V 60Hz", "+1-868", "left", "990", "safe", "TTD", 10.6596, -61.5086, "America/Port_of_Spain"),
        ("TN", "C,E", "230V 50Hz", "+216", "right", "197", "safe", "TND", 36.8065, 10.1815, "Africa/Tunis"),
        ("TR", "C,F", "230V 50Hz", "+90", "right", "112", "safe", "TRY", 39.9334, 32.8597, "Europe/Istanbul"),
        ("TM", "C,F", "220V 50Hz", "+993", "right", "03", "caution", "TMT", 37.9601, 58.3261, "Asia/Ashgabat"),
        ("TV", "I", "220V 50Hz", "+688", "left", "911", "caution", "AUD", -8.5211, 179.1983, "Pacific/Funafuti"),
        ("UG", "G", "240V 50Hz", "+256", "left", "999", "unsafe", "UGX", 0.3476, 32.5825, "Africa/Kampala"),
        ("UA", "C,F", "230V 50Hz", "+380", "right", "112", "caution", "UAH", 50.4501, 30.5234, "Europe/Kyiv"),
        ("AE", "C,D,G", "220V 50Hz", "+971", "right", "999", "safe", "AED", 24.4539, 54.3773, "Asia/Dubai"),
        ("GB", "G", "230V 50Hz", "+44", "left", "999", "safe", "GBP", 51.5074, -0.1278, "Europe/London"),
        ("US", "A,B", "120V 60Hz", "+1", "right", "911", "safe", "USD", 38.9072, -77.0369, "America/New_York"),
        ("UY", "C,F,I,L", "220V 50Hz", "+598", "right", "911", "safe", "UYU", -34.9011, -56.1645, "America/Montevideo"),
        ("UZ", "C,F", "220V 50Hz", "+998", "right", "101", "caution", "UZS", 41.2995, 69.2401, "Asia/Tashkent"),
        ("VU", "C,G,I", "220V 50Hz", "+678", "right", "112", "caution", "VUV", -17.7334, 168.3273, "Pacific/Efate"),
        ("VE", "A,B", "120V 60Hz", "+58", "right", "171", "caution", "VES", 10.4806, -66.9036, "America/Caracas"),
        ("VN", "A,C,G", "220V 50Hz", "+84", "right", "113", "caution", "VND", 21.0278, 105.8342, "Asia/Ho_Chi_Minh"),
        ("YE", "A,D,G", "230V 50Hz", "+967", "right", "199", "unsafe", "YER", 15.3694, 44.1910, "Asia/Aden"),
        ("ZM", "C,D,G", "230V 50Hz", "+260", "left", "999", "unsafe", "ZMW", -15.3875, 28.3228, "Africa/Lusaka"),
        ("ZW", "D,G", "220V 50Hz", "+263", "left", "999", "unsafe", "ZWL", -17.8292, 31.0522, "Africa/Harare"),
    ]
    # fmt: on

    conn = op.get_bind()
    for row in countries:
        (
            iso,
            sockets,
            volt,
            phone,
            driving,
            emergency,
            water,
            currency,
            lat,
            lng,
            tz,
        ) = row
        conn.execute(
            sa.text(
                "UPDATE un_countries SET "
                "socket_types = :sockets, voltage = :volt, phone_code = :phone, "
                "driving_side = :driving, emergency_number = :emergency, "
                "tap_water = :water, currency_code = :currency, "
                "capital_lat = :lat, capital_lng = :lng, timezone = :tz "
                "WHERE iso_alpha2 = :iso"
            ),
            {
                "iso": iso,
                "sockets": sockets,
                "volt": volt,
                "phone": phone,
                "driving": driving,
                "emergency": emergency,
                "water": water,
                "currency": currency,
                "lat": lat,
                "lng": lng,
                "tz": tz,
            },
        )


def downgrade() -> None:
    op.drop_column("un_countries", "timezone")
    op.drop_column("un_countries", "capital_lng")
    op.drop_column("un_countries", "capital_lat")
    op.drop_column("un_countries", "currency_code")
    op.drop_column("un_countries", "tap_water")
    op.drop_column("un_countries", "emergency_number")
    op.drop_column("un_countries", "driving_side")
    op.drop_column("un_countries", "phone_code")
    op.drop_column("un_countries", "voltage")
    op.drop_column("un_countries", "socket_types")
