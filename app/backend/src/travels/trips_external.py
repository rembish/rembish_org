import calendar
import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from cachetools import TTLCache

from .models import CountryHoliday, SunriseSunset

# TTL caches for external API responses (auto-evict expired entries, bounded size)
_holidays_cache: TTLCache[tuple[int, str], list[dict]] = TTLCache(maxsize=256, ttl=86400)
_currency_cache: TTLCache[str, dict[str, float] | None] = TTLCache(maxsize=64, ttl=3600)
_weather_cache: TTLCache[tuple[float, float, int], dict[str, float | None | int]] = TTLCache(
    maxsize=256, ttl=86400
)
_sunrise_cache: TTLCache[tuple[float, float, str], SunriseSunset | None] = TTLCache(
    maxsize=256, ttl=86400
)

log = logging.getLogger(__name__)

_CURRENCY_NAMES: dict[str, str] = {
    "AED": "UAE Dirham",
    "AFN": "Afghani",
    "ALL": "Lek",
    "AMD": "Armenian Dram",
    "ANG": "Netherlands Antillean Guilder",
    "AOA": "Kwanza",
    "ARS": "Argentine Peso",
    "AUD": "Australian Dollar",
    "AWG": "Aruban Florin",
    "AZN": "Azerbaijani Manat",
    "BAM": "Convertible Mark",
    "BBD": "Barbados Dollar",
    "BDT": "Taka",
    "BGN": "Bulgarian Lev",
    "BHD": "Bahraini Dinar",
    "BIF": "Burundi Franc",
    "BMD": "Bermudian Dollar",
    "BND": "Brunei Dollar",
    "BOB": "Boliviano",
    "BRL": "Brazilian Real",
    "BSD": "Bahamian Dollar",
    "BTN": "Ngultrum",
    "BWP": "Pula",
    "BYN": "Belarusian Ruble",
    "BZD": "Belize Dollar",
    "CAD": "Canadian Dollar",
    "CDF": "Congolese Franc",
    "CHF": "Swiss Franc",
    "CLP": "Chilean Peso",
    "CNY": "Yuan Renminbi",
    "COP": "Colombian Peso",
    "CRC": "Costa Rican Colon",
    "CUP": "Cuban Peso",
    "CVE": "Cabo Verde Escudo",
    "CZK": "Czech Koruna",
    "DJF": "Djibouti Franc",
    "DKK": "Danish Krone",
    "DOP": "Dominican Peso",
    "DZD": "Algerian Dinar",
    "EGP": "Egyptian Pound",
    "ERN": "Nakfa",
    "ETB": "Ethiopian Birr",
    "EUR": "Euro",
    "FJD": "Fiji Dollar",
    "FKP": "Falkland Islands Pound",
    "GBP": "Pound Sterling",
    "GEL": "Lari",
    "GHS": "Ghana Cedi",
    "GIP": "Gibraltar Pound",
    "GMD": "Dalasi",
    "GNF": "Guinean Franc",
    "GTQ": "Quetzal",
    "GYD": "Guyana Dollar",
    "HKD": "Hong Kong Dollar",
    "HNL": "Lempira",
    "HRK": "Kuna",
    "HTG": "Gourde",
    "HUF": "Forint",
    "IDR": "Rupiah",
    "ILS": "New Israeli Sheqel",
    "INR": "Indian Rupee",
    "IQD": "Iraqi Dinar",
    "IRR": "Iranian Rial",
    "ISK": "Iceland Krona",
    "JMD": "Jamaican Dollar",
    "JOD": "Jordanian Dinar",
    "JPY": "Yen",
    "KES": "Kenyan Shilling",
    "KGS": "Som",
    "KHR": "Riel",
    "KMF": "Comorian Franc",
    "KPW": "North Korean Won",
    "KRW": "Won",
    "KWD": "Kuwaiti Dinar",
    "KYD": "Cayman Islands Dollar",
    "KZT": "Tenge",
    "LAK": "Lao Kip",
    "LBP": "Lebanese Pound",
    "LKR": "Sri Lanka Rupee",
    "LRD": "Liberian Dollar",
    "LSL": "Loti",
    "LYD": "Libyan Dinar",
    "MAD": "Moroccan Dirham",
    "MDL": "Moldovan Leu",
    "MGA": "Malagasy Ariary",
    "MKD": "Denar",
    "MMK": "Kyat",
    "MNT": "Tugrik",
    "MOP": "Pataca",
    "MRU": "Ouguiya",
    "MUR": "Mauritius Rupee",
    "MVR": "Rufiyaa",
    "MWK": "Malawi Kwacha",
    "MXN": "Mexican Peso",
    "MYR": "Malaysian Ringgit",
    "MZN": "Mozambique Metical",
    "NAD": "Namibia Dollar",
    "NGN": "Naira",
    "NIO": "Cordoba Oro",
    "NOK": "Norwegian Krone",
    "NPR": "Nepalese Rupee",
    "NZD": "New Zealand Dollar",
    "OMR": "Rial Omani",
    "PAB": "Balboa",
    "PEN": "Sol",
    "PGK": "Kina",
    "PHP": "Philippine Peso",
    "PKR": "Pakistan Rupee",
    "PLN": "Zloty",
    "PYG": "Guarani",
    "QAR": "Qatari Rial",
    "RON": "Romanian Leu",
    "RSD": "Serbian Dinar",
    "RUB": "Russian Ruble",
    "RWF": "Rwanda Franc",
    "SAR": "Saudi Riyal",
    "SBD": "Solomon Islands Dollar",
    "SCR": "Seychelles Rupee",
    "SDG": "Sudanese Pound",
    "SEK": "Swedish Krona",
    "SGD": "Singapore Dollar",
    "SHP": "Saint Helena Pound",
    "SLE": "Leone",
    "SOS": "Somali Shilling",
    "SRD": "Surinam Dollar",
    "SSP": "South Sudanese Pound",
    "STN": "Dobra",
    "SVC": "El Salvador Colon",
    "SYP": "Syrian Pound",
    "SZL": "Lilangeni",
    "THB": "Baht",
    "TJS": "Somoni",
    "TMT": "Turkmenistan Manat",
    "TND": "Tunisian Dinar",
    "TOP": "Pa'anga",
    "TRY": "Turkish Lira",
    "TTD": "Trinidad and Tobago Dollar",
    "TWD": "New Taiwan Dollar",
    "TZS": "Tanzanian Shilling",
    "UAH": "Hryvnia",
    "UGX": "Uganda Shilling",
    "USD": "US Dollar",
    "UYU": "Peso Uruguayo",
    "UZS": "Uzbekistan Sum",
    "VES": "Bolivar Soberano",
    "VND": "Dong",
    "VUV": "Vatu",
    "WST": "Tala",
    "XAF": "CFA Franc BEAC",
    "XCD": "East Caribbean Dollar",
    "XOF": "CFA Franc BCEAO",
    "XPF": "CFP Franc",
    "YER": "Yemeni Rial",
    "ZAR": "Rand",
    "ZMW": "Zambian Kwacha",
    "ZWL": "Zimbabwe Dollar",
}


def _get_currency_name(code: str) -> str | None:
    return _CURRENCY_NAMES.get(code)


def _fetch_currency_rates(currency_code: str) -> dict[str, float] | None:
    """Fetch exchange rates with caching.

    Uses Frankfurter (ECB) for supported currencies, falls back to
    open.er-api.com (free, no key, 150+ currencies) for others.
    """
    if currency_code in _currency_cache:
        return _currency_cache[currency_code]

    # ECB-supported currencies via Frankfurter (more reliable)
    ecb_supported = {
        "AUD",
        "BGN",
        "BRL",
        "CAD",
        "CHF",
        "CNY",
        "CZK",
        "DKK",
        "EUR",
        "GBP",
        "HKD",
        "HUF",
        "IDR",
        "ILS",
        "INR",
        "ISK",
        "JPY",
        "KRW",
        "MXN",
        "MYR",
        "NOK",
        "NZD",
        "PHP",
        "PLN",
        "RON",
        "SEK",
        "SGD",
        "THB",
        "TRY",
        "USD",
        "ZAR",
    }

    rates = _fetch_frankfurter(currency_code) if currency_code in ecb_supported else None
    if rates is None:
        rates = _fetch_open_er(currency_code)

    _currency_cache[currency_code] = rates
    return rates


def _fetch_frankfurter(currency_code: str) -> dict[str, float] | None:
    """Fetch from Frankfurter API (ECB data, 31 currencies)."""
    try:
        targets = {"CZK", "EUR", "USD"} - {currency_code}
        resp = httpx.get(
            f"https://api.frankfurter.app/latest?from={currency_code}&to={','.join(sorted(targets))}",
            timeout=5.0,
        )
        resp.raise_for_status()
        rates: dict[str, float] = resp.json().get("rates", {})
        rates[currency_code] = 1.0
        return rates
    except Exception:
        log.warning("Frankfurter failed for %s", currency_code)
        return None


def _fetch_open_er(currency_code: str) -> dict[str, float] | None:
    """Fetch from open.er-api.com (free, no key, 150+ currencies)."""
    try:
        resp = httpx.get(
            f"https://open.er-api.com/v6/latest/{currency_code}",
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") != "success":
            return None
        all_rates = data.get("rates", {})
        # Extract only the currencies we care about
        result: dict[str, float] = {}
        for target in ("CZK", "EUR", "USD", currency_code):
            if target in all_rates:
                result[target] = all_rates[target]
        return result if result else None
    except Exception:
        log.warning("open.er-api failed for %s", currency_code)
        return None


def _fetch_weather(lat: float, lng: float, month: int) -> dict[str, float | None | int]:
    """Fetch climate averages from Open-Meteo Climate API with caching."""
    # Round coords to 2 decimal places for cache key stability
    cache_key = (round(lat, 2), round(lng, 2), month)
    cached_data = _weather_cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Use a representative year range for climate data
    year = 2020
    last_day = min(28, calendar.monthrange(year, month)[1])
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{last_day:02d}"

    try:
        resp = httpx.get(
            "https://climate-api.open-meteo.com/v1/climate",
            params={
                "latitude": lat,
                "longitude": lng,
                "start_date": start,
                "end_date": end,
                "daily": ",".join(
                    [
                        "temperature_2m_mean",
                        "temperature_2m_min",
                        "temperature_2m_max",
                        "precipitation_sum",
                    ]
                ),
                "models": "EC_Earth3P_HR",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        daily = resp.json().get("daily", {})
        temps = [t for t in (daily.get("temperature_2m_mean") or []) if t is not None]
        mins = [t for t in (daily.get("temperature_2m_min") or []) if t is not None]
        maxs = [t for t in (daily.get("temperature_2m_max") or []) if t is not None]
        precip = [p for p in (daily.get("precipitation_sum") or []) if p is not None]
        rainy = sum(1 for p in precip if p > 0.5)

        result: dict[str, float | None | int] = {
            "avg_temp_c": round(sum(temps) / len(temps), 1) if temps else None,
            "min_temp_c": round(sum(mins) / len(mins), 1) if mins else None,
            "max_temp_c": round(sum(maxs) / len(maxs), 1) if maxs else None,
            "avg_precipitation_mm": round(sum(precip) / len(precip), 1) if precip else None,
            "rainy_days": rainy if precip else None,
        }
        _weather_cache[cache_key] = result
        return result
    except Exception:
        log.warning("Failed to fetch weather for (%.2f, %.2f, %d)", lat, lng, month)
        fallback: dict[str, float | None | int] = {
            "avg_temp_c": None,
            "min_temp_c": None,
            "max_temp_c": None,
            "avg_precipitation_mm": None,
            "rainy_days": None,
        }
        _weather_cache[cache_key] = fallback
        return fallback


def _fetch_sunrise_sunset(
    lat: float, lng: float, trip_date: date, tz_offset: float | None
) -> SunriseSunset | None:
    """Fetch sunrise/sunset for a location and date."""
    date_str = trip_date.isoformat()
    cache_key = (round(lat, 2), round(lng, 2), date_str)
    if cache_key in _sunrise_cache:
        return _sunrise_cache[cache_key]

    try:
        resp = httpx.get(
            "https://api.sunrise-sunset.org/json",
            params={
                "lat": lat,
                "lng": lng,
                "date": date_str,
                "formatted": 0,
            },
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK":
            _sunrise_cache[cache_key] = None
            return None

        results = data["results"]
        sunrise_utc = results["sunrise"]  # ISO 8601
        sunset_utc = results["sunset"]
        day_length = results.get("day_length", 0)

        # Parse UTC times and apply timezone offset
        offset_h = tz_offset if tz_offset is not None else 0
        # tz_offset is relative to CET; compute actual UTC offset
        # CET = UTC+1 (winter) or UTC+2 (summer)
        try:
            cet = ZoneInfo("Europe/Prague")
            cet_offset = datetime(
                trip_date.year, trip_date.month, trip_date.day, 12, tzinfo=cet
            ).utcoffset()
            cet_h = cet_offset.total_seconds() / 3600 if cet_offset else 1
        except Exception:
            cet_h = 1
        country_utc_offset = cet_h + offset_h

        tz = timezone(timedelta(hours=country_utc_offset))
        sr = datetime.fromisoformat(sunrise_utc).astimezone(tz)
        ss = datetime.fromisoformat(sunset_utc).astimezone(tz)

        result = SunriseSunset(
            sunrise=sr.strftime("%H:%M"),
            sunset=ss.strftime("%H:%M"),
            day_length_hours=round(day_length / 3600, 1),
        )
        _sunrise_cache[cache_key] = result
        return result
    except Exception:
        log.warning("Failed sunrise/sunset for (%.2f, %.2f, %s)", lat, lng, date_str)
        _sunrise_cache[cache_key] = None
        return None


def _fetch_holidays_for_country(country_code: str, start: date, end: date) -> list[CountryHoliday]:
    """Fetch public holidays for a country within a date range."""
    holidays: list[CountryHoliday] = []

    # Determine years to fetch
    years = set()
    for y in range(start.year, end.year + 1):
        years.add(y)

    for year in sorted(years):
        cache_key = (year, country_code.upper())

        # Check cache
        raw_holidays: list[dict] = []
        if cache_key in _holidays_cache:
            raw_holidays = _holidays_cache[cache_key]
        else:
            raw_holidays = _fetch_holidays_raw(year, country_code)

        for h in raw_holidays:
            h_date = h.get("date", "")
            if h_date and start.isoformat() <= h_date <= end.isoformat():
                holidays.append(
                    CountryHoliday(
                        date=h_date,
                        name=h.get("name", ""),
                        local_name=h.get("localName"),
                    )
                )

    return sorted(holidays, key=lambda h: h.date)


def _fetch_holidays_raw(year: int, country_code: str) -> list[dict]:
    """Fetch raw holidays from Nager.Date API and cache them."""
    cache_key = (year, country_code.upper())
    try:
        resp = httpx.get(
            f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code.upper()}",
            timeout=10.0,
        )
        if resp.status_code in (204, 404):
            _holidays_cache[cache_key] = []
            return []
        resp.raise_for_status()
        data: list[dict] = resp.json()
        _holidays_cache[cache_key] = data
        return data
    except Exception:
        _holidays_cache[cache_key] = []
        return []
