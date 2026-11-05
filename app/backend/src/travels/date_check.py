"""Sanity checks for AI-extracted dates against the trip they are uploaded to.

Tickets and boarding passes often print dates without a year ("13NOV"), so the
extractor may guess the wrong one. Dates are compared with the trip window: a
wrong year that fits once replaced by the trip's year is corrected, anything
else outside the window is flagged for the user to review.
"""

from datetime import date, datetime, timedelta

# Bookings may legitimately start a little before / end a little after the trip
# (evening departures, overnight arrivals, airport hotels).
SLACK_DAYS = 3


def trip_window(start: date, end: date | None) -> tuple[date, date]:
    return start, end or start


def _parse(value: str) -> tuple[date, str] | None:
    """Split 'YYYY-MM-DD[ HH:MM]' into a date and the remaining suffix."""
    head, suffix = value[:10], value[10:]
    try:
        return datetime.strptime(head, "%Y-%m-%d").date(), suffix
    except ValueError:
        return None


def _in_window(d: date, start: date, end: date) -> bool:
    return start - timedelta(days=SLACK_DAYS) <= d <= end + timedelta(days=SLACK_DAYS)


def year_shift(value: str | None, start: date, end: date) -> int | None:
    """Years to add so the date lands in the trip window.

    0 if the date already fits, None if it cannot be parsed or no year fits.
    """
    if not value:
        return 0
    parsed = _parse(value)
    if not parsed:
        return None
    d, _ = parsed
    if _in_window(d, start, end):
        return 0
    for year in sorted({start.year, end.year}):
        try:
            candidate = d.replace(year=year)
        except ValueError:  # 29 Feb in a non-leap year
            continue
        if _in_window(candidate, start, end):
            return year - d.year
    return None


def shift_years(value: str | None, years: int) -> str | None:
    """Move a 'YYYY-MM-DD[ HH:MM]' value by whole years (no-op for 0/None)."""
    if not value or not years:
        return value
    parsed = _parse(value)
    if not parsed:
        return value
    d, suffix = parsed
    try:
        return d.replace(year=d.year + years).isoformat() + suffix
    except ValueError:
        return value


def check_dates(
    values: dict[str, str | None], start: date, end: date | None
) -> tuple[dict[str, str | None], str | None]:
    """Validate the date fields of one extracted item against the trip.

    The first non-empty field is the anchor (departure / pickup / check-in): if
    its year is off, all fields move by the same number of years so durations
    and overnight arrivals stay intact. Returns the (possibly corrected) values
    and a human-readable warning, or None when everything fits.
    """
    start, end = trip_window(start, end)
    anchor = next((k for k, v in values.items() if v), None)
    if anchor is None:
        return values, None

    shift = year_shift(values[anchor], start, end)
    window = f"{start.isoformat()} – {end.isoformat()}"
    if shift is None:
        return values, f"Date {values[anchor]} is outside the trip ({window}) — please check"
    if shift == 0:
        outside = [k for k, v in values.items() if v and year_shift(v, start, end) != 0]
        if outside:
            return (
                values,
                f"Date {values[outside[0]]} is outside the trip ({window}) — please check",
            )
        return values, None

    fixed = {k: shift_years(v, shift) for k, v in values.items()}
    old_year = values[anchor][:4]  # type: ignore[index]
    new_year = fixed[anchor][:4]  # type: ignore[index]
    return fixed, f"Year corrected from {old_year} to {new_year} to match the trip ({window})"
