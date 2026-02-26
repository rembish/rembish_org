"""Travel advisories: static event computation for trip info tab.

Covers religious observances, cultural festivals, and major sporting events.
All dates computed from static data — no paid APIs.
"""

from datetime import date, timedelta
from typing import Literal

from hijridate import Gregorian, Hijri

from .models import TravelAdvisory

# ---------------------------------------------------------------------------
# Country sets
# ---------------------------------------------------------------------------

RAMADAN_TIER1 = {"SA", "IR", "KW", "QA", "OM", "PK", "BN", "IQ"}
RAMADAN_TIER2 = {"JO", "MA", "EG", "DZ", "TN", "BD", "MY"}
RAMADAN_TIER3 = {"AE", "TR", "ID", "LB"}
ALL_RAMADAN = RAMADAN_TIER1 | RAMADAN_TIER2 | RAMADAN_TIER3

# Eid countries: union of all Ramadan tiers
ALL_EID = ALL_RAMADAN

CARNIVAL_COUNTRIES: dict[str, str | None] = {
    "BR": None,
    "IT": "Venice",
    "DE": "Cologne",
}

CNY_COUNTRIES = {"CN", "SG", "MY", "TW", "VN"}

# ---------------------------------------------------------------------------
# Hardcoded date tables (2024–2030)
# ---------------------------------------------------------------------------

NYEPI_DATES: dict[int, date] = {
    2024: date(2024, 3, 11),
    2025: date(2025, 3, 29),
    2026: date(2026, 3, 19),
    2027: date(2027, 3, 8),
    2028: date(2028, 3, 26),
    2029: date(2029, 3, 15),
    2030: date(2030, 3, 5),
}

THAI_ALCOHOL_BAN_DATES: dict[int, list[date]] = {
    2024: [
        date(2024, 2, 24),  # Makha Bucha
        date(2024, 5, 22),  # Visakha Bucha
        date(2024, 7, 20),  # Asalha Bucha
        date(2024, 7, 21),  # Buddhist Lent
        date(2024, 10, 17),  # End of Buddhist Lent
    ],
    2025: [
        date(2025, 2, 12),
        date(2025, 5, 11),
        date(2025, 7, 10),
        date(2025, 7, 11),
        date(2025, 10, 7),
    ],
    2026: [
        date(2026, 3, 3),
        date(2026, 5, 31),
        date(2026, 7, 29),
        date(2026, 7, 30),
        date(2026, 10, 26),
    ],
    2027: [
        date(2027, 2, 20),
        date(2027, 5, 20),
        date(2027, 7, 18),
        date(2027, 7, 19),
        date(2027, 10, 15),
    ],
    2028: [
        date(2028, 2, 9),
        date(2028, 5, 8),
        date(2028, 7, 6),
        date(2028, 7, 7),
        date(2028, 10, 3),
    ],
    2029: [
        date(2029, 1, 29),
        date(2029, 4, 27),
        date(2029, 6, 25),
        date(2029, 6, 26),
        date(2029, 9, 22),
    ],
    2030: [
        date(2030, 2, 17),
        date(2030, 5, 17),
        date(2030, 7, 15),
        date(2030, 7, 16),
        date(2030, 10, 12),
    ],
}

HOLI_DATES: dict[int, date] = {
    2024: date(2024, 3, 25),
    2025: date(2025, 3, 14),
    2026: date(2026, 3, 3),
    2027: date(2027, 3, 22),
    2028: date(2028, 3, 11),
    2029: date(2029, 3, 1),
    2030: date(2030, 3, 20),
}

CNY_DATES: dict[int, date] = {
    2024: date(2024, 2, 10),
    2025: date(2025, 1, 29),
    2026: date(2026, 2, 17),
    2027: date(2027, 2, 6),
    2028: date(2028, 1, 26),
    2029: date(2029, 2, 13),
    2030: date(2030, 2, 3),
}

DIWALI_DATES: dict[int, date] = {
    2024: date(2024, 11, 1),
    2025: date(2025, 10, 20),
    2026: date(2026, 11, 8),
    2027: date(2027, 10, 29),
    2028: date(2028, 10, 17),
    2029: date(2029, 11, 5),
    2030: date(2030, 10, 26),
}

# Major sporting events: list of (name, country_codes, start, end, severity)
MAJOR_SPORTING_EVENTS: list[tuple[str, set[str], date, date, Literal["high", "medium", "low"]]] = [
    ("Summer Olympics", {"FR"}, date(2024, 7, 26), date(2024, 8, 11), "medium"),
    ("Winter Olympics", {"IT"}, date(2026, 2, 6), date(2026, 2, 22), "medium"),
    ("Summer Olympics", {"US"}, date(2028, 7, 14), date(2028, 7, 30), "medium"),
    ("Summer Olympics", {"AU"}, date(2032, 7, 23), date(2032, 8, 8), "medium"),
    (
        "FIFA World Cup",
        {"US", "CA", "MX"},
        date(2026, 6, 11),
        date(2026, 7, 19),
        "medium",
    ),
    (
        "FIFA World Cup",
        {"ES", "PT", "MA"},
        date(2030, 6, 13),
        date(2030, 7, 21),
        "medium",
    ),
]


# ---------------------------------------------------------------------------
# Date computation helpers
# ---------------------------------------------------------------------------


def _easter_date(year: int) -> date:
    """Compute Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _ramadan_dates(year: int) -> tuple[date, date] | None:
    """Return Gregorian start/end of Ramadan overlapping the given year."""
    # Check Hijri years that might overlap this Gregorian year
    # Ramadan is month 9 in the Hijri calendar
    hijri_year_approx = Gregorian(year, 1, 1).to_hijri().year
    for hy in range(hijri_year_approx - 1, hijri_year_approx + 2):
        try:
            start = Hijri(hy, 9, 1).to_gregorian()
            end = Hijri(hy, 9, 29).to_gregorian()
            # Try 30th day (Ramadan can be 29 or 30 days)
            try:
                end = Hijri(hy, 9, 30).to_gregorian()
            except (ValueError, OverflowError):
                pass
            start_d = date(start.year, start.month, start.day)
            end_d = date(end.year, end.month, end.day)
            if start_d.year == year or end_d.year == year:
                return (start_d, end_d)
        except (ValueError, OverflowError):
            continue
    return None


def _eid_al_fitr_dates(year: int) -> tuple[date, date] | None:
    """Return Eid al-Fitr dates (3 days starting Shawwal 1)."""
    hijri_year_approx = Gregorian(year, 1, 1).to_hijri().year
    for hy in range(hijri_year_approx - 1, hijri_year_approx + 2):
        try:
            start = Hijri(hy, 10, 1).to_gregorian()
            start_d = date(start.year, start.month, start.day)
            end_d = start_d + timedelta(days=2)
            if start_d.year == year or end_d.year == year:
                return (start_d, end_d)
        except (ValueError, OverflowError):
            continue
    return None


def _eid_al_adha_dates(year: int) -> tuple[date, date] | None:
    """Return Eid al-Adha dates (4 days starting Dhul Hijjah 10)."""
    hijri_year_approx = Gregorian(year, 1, 1).to_hijri().year
    for hy in range(hijri_year_approx - 1, hijri_year_approx + 2):
        try:
            start = Hijri(hy, 12, 10).to_gregorian()
            start_d = date(start.year, start.month, start.day)
            end_d = start_d + timedelta(days=3)
            if start_d.year == year or end_d.year == year:
                return (start_d, end_d)
        except (ValueError, OverflowError):
            continue
    return None


def _carnival_dates(year: int) -> tuple[date, date]:
    """Carnival: Friday before to Tuesday before Ash Wednesday (47 days before Easter)."""
    easter = _easter_date(year)
    # Carnival Saturday to Shrove Tuesday (47 days before Easter is Shrove Tuesday)
    shrove_tuesday = easter - timedelta(days=47)
    carnival_start = shrove_tuesday - timedelta(days=3)  # Saturday
    return (carnival_start, shrove_tuesday)


def _oktoberfest_dates(year: int) -> tuple[date, date]:
    """Oktoberfest: ~Sep 16 to first Sunday of October."""
    start = date(year, 9, 16)
    # First Sunday of October
    oct1 = date(year, 10, 1)
    days_until_sunday = (6 - oct1.weekday()) % 7
    first_sunday_oct = oct1 + timedelta(days=days_until_sunday)
    return (start, first_sunday_oct)


def _overlaps(event_start: date, event_end: date, trip_start: date, trip_end: date) -> bool:
    """Check if two date ranges overlap."""
    return event_start <= trip_end and event_end >= trip_start


# ---------------------------------------------------------------------------
# Per-event check functions
# ---------------------------------------------------------------------------


def _check_ramadan(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso not in ALL_RAMADAN:
        return
    severity: Literal["high", "medium", "low"]
    if iso in RAMADAN_TIER1:
        severity = "high"
        summary = "Public eating/drinking illegal during daytime"
    elif iso in RAMADAN_TIER2:
        severity = "medium"
        summary = "Most restaurants closed during daytime"
    else:
        severity = "low"
        summary = "Ramadan observed; tourist areas mostly unaffected"

    for y in years:
        dates = _ramadan_dates(y)
        if dates and _overlaps(dates[0], dates[1], trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Ramadan",
                    category="restriction",
                    start_date=dates[0].isoformat(),
                    end_date=dates[1].isoformat(),
                    severity=severity,
                    summary=summary,
                )
            )
            return  # Only one Ramadan per query


def _check_eid_al_fitr(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso not in ALL_EID:
        return
    for y in years:
        dates = _eid_al_fitr_dates(y)
        if dates and _overlaps(dates[0], dates[1], trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Eid al-Fitr",
                    category="restriction",
                    start_date=dates[0].isoformat(),
                    end_date=dates[1].isoformat(),
                    severity="medium",
                    summary="3-day public holiday; government offices and many businesses closed",
                )
            )
            return


def _check_eid_al_adha(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso not in ALL_EID:
        return
    for y in years:
        dates = _eid_al_adha_dates(y)
        if dates and _overlaps(dates[0], dates[1], trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Eid al-Adha",
                    category="restriction",
                    start_date=dates[0].isoformat(),
                    end_date=dates[1].isoformat(),
                    severity="medium",
                    summary="4-day public holiday; government offices and many businesses closed",
                )
            )
            return


def _check_nyepi(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "ID":
        return
    for y in years:
        d = NYEPI_DATES.get(y)
        if d and _overlaps(d, d, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Nyepi (Day of Silence)",
                    category="restriction",
                    start_date=d.isoformat(),
                    end_date=d.isoformat(),
                    severity="high",
                    summary="24h island-wide shutdown; airport closed, no outdoor activity",
                    details="All flights cancelled. Hotels enforce staying indoors.",
                )
            )
            return


def _check_thai_alcohol_bans(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "TH":
        return
    for y in years:
        ban_dates = THAI_ALCOHOL_BAN_DATES.get(y, [])
        for d in ban_dates:
            if _overlaps(d, d, trip_start, trip_end):
                results.append(
                    TravelAdvisory(
                        event_name="Buddhist Holiday (Alcohol Ban)",
                        category="restriction",
                        start_date=d.isoformat(),
                        end_date=d.isoformat(),
                        severity="medium",
                        summary="Alcohol sales banned 00:00–00:00; hotels and airports exempt",
                    )
                )


def _check_carnival(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso not in CARNIVAL_COUNTRIES:
        return
    location = CARNIVAL_COUNTRIES[iso]
    for y in years:
        start, end = _carnival_dates(y)
        if _overlaps(start, end, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Carnival",
                    category="event",
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                    severity="low",
                    summary="Major festival with parades and street parties",
                    location=location,
                )
            )
            return


def _check_songkran(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "TH":
        return
    for y in years:
        start = date(y, 4, 13)
        end = date(y, 4, 15)
        if _overlaps(start, end, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Songkran (Water Festival)",
                    category="event",
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                    severity="low",
                    summary="Thai New Year water festival; expect street water fights",
                )
            )
            return


def _check_holi(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "IN":
        return
    for y in years:
        d = HOLI_DATES.get(y)
        if d and _overlaps(d, d, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Holi (Festival of Colors)",
                    category="event",
                    start_date=d.isoformat(),
                    end_date=d.isoformat(),
                    severity="low",
                    summary="Colorful spring festival; expect colored powder and water",
                )
            )
            return


def _check_cny(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso not in CNY_COUNTRIES:
        return
    for y in years:
        d = CNY_DATES.get(y)
        if d:
            # CNY celebrations span about a week
            start = d
            end = d + timedelta(days=6)
            if _overlaps(start, end, trip_start, trip_end):
                results.append(
                    TravelAdvisory(
                        event_name="Chinese New Year",
                        category="event",
                        start_date=start.isoformat(),
                        end_date=end.isoformat(),
                        severity="low",
                        summary="Major holiday week; heavy travel, some businesses closed",
                    )
                )
                return


def _check_diwali(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "IN":
        return
    for y in years:
        d = DIWALI_DATES.get(y)
        if d:
            # Diwali celebrations span ~5 days
            start = d - timedelta(days=2)
            end = d + timedelta(days=2)
            if _overlaps(start, end, trip_start, trip_end):
                results.append(
                    TravelAdvisory(
                        event_name="Diwali (Festival of Lights)",
                        category="event",
                        start_date=start.isoformat(),
                        end_date=end.isoformat(),
                        severity="low",
                        summary="Festival of Lights; fireworks, lights, and celebrations",
                    )
                )
                return


def _check_oktoberfest(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "DE":
        return
    for y in years:
        start, end = _oktoberfest_dates(y)
        if _overlaps(start, end, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Oktoberfest",
                    category="event",
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                    severity="low",
                    summary="World's largest beer festival in Munich",
                    location="Munich",
                )
            )
            return


def _check_day_of_dead(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "MX":
        return
    for y in years:
        start = date(y, 11, 1)
        end = date(y, 11, 2)
        if _overlaps(start, end, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="Day of the Dead",
                    category="event",
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                    severity="low",
                    summary="Traditional celebration honoring deceased; parades and altars",
                )
            )
            return


def _check_san_fermin(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "ES":
        return
    for y in years:
        start = date(y, 7, 6)
        end = date(y, 7, 14)
        if _overlaps(start, end, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="San Fermin",
                    category="event",
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                    severity="low",
                    summary="Running of the Bulls festival",
                    location="Pamplona",
                )
            )
            return


def _check_st_patricks(
    iso: str, trip_start: date, trip_end: date, years: set[int], results: list[TravelAdvisory]
) -> None:
    if iso != "IE":
        return
    for y in years:
        d = date(y, 3, 17)
        if _overlaps(d, d, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name="St Patrick's Day",
                    category="event",
                    start_date=d.isoformat(),
                    end_date=d.isoformat(),
                    severity="low",
                    summary="National holiday with parades and celebrations",
                )
            )
            return


def _check_sporting_events(
    iso: str, trip_start: date, trip_end: date, results: list[TravelAdvisory]
) -> None:
    for name, countries, start, end, severity in MAJOR_SPORTING_EVENTS:
        if iso in countries and _overlaps(start, end, trip_start, trip_end):
            results.append(
                TravelAdvisory(
                    event_name=name,
                    category="event",
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                    severity=severity,
                    summary=f"{name} host country; expect crowds and price surges",
                )
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def get_travel_advisories(
    iso_alpha2: str, trip_start: date, trip_end: date
) -> list[TravelAdvisory]:
    """Return travel advisories for a country overlapping the trip dates."""
    if not iso_alpha2:
        return []

    iso = iso_alpha2.upper()
    years = set(range(trip_start.year, trip_end.year + 1))
    results: list[TravelAdvisory] = []

    # Restriction events
    _check_ramadan(iso, trip_start, trip_end, years, results)
    _check_eid_al_fitr(iso, trip_start, trip_end, years, results)
    _check_eid_al_adha(iso, trip_start, trip_end, years, results)
    _check_nyepi(iso, trip_start, trip_end, years, results)
    _check_thai_alcohol_bans(iso, trip_start, trip_end, years, results)

    # Major events
    _check_carnival(iso, trip_start, trip_end, years, results)
    _check_songkran(iso, trip_start, trip_end, years, results)
    _check_holi(iso, trip_start, trip_end, years, results)
    _check_cny(iso, trip_start, trip_end, years, results)
    _check_diwali(iso, trip_start, trip_end, years, results)
    _check_oktoberfest(iso, trip_start, trip_end, years, results)
    _check_day_of_dead(iso, trip_start, trip_end, years, results)
    _check_san_fermin(iso, trip_start, trip_end, years, results)
    _check_st_patricks(iso, trip_start, trip_end, years, results)
    _check_sporting_events(iso, trip_start, trip_end, results)

    # Sort: restrictions first, then events; within each group by start_date
    category_order = {"restriction": 0, "event": 1}
    results.sort(key=lambda a: (category_order.get(a.category, 2), a.start_date))

    return results
