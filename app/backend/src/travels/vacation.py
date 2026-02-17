"""Vacation day calculator.

Ported from amifree/backend/app/services/calculator.py.
Calculates vacation days consumed by trips, accounting for
departure/arrival times, weekends, and public holidays.
"""

from datetime import date, timedelta

ANNUAL_LEAVE_DAYS = 30

# Departure multiplier: how much of the departure day counts as vacation
_DEPARTURE_MULTIPLIER = {
    "morning": 1.0,  # Leave at 9:00 → full day
    "midday": 0.5,  # Leave at 13:00 → half day
    "evening": 0.0,  # Leave at 17:00 → no vacation used
}

# Arrival multiplier: how much of the arrival day counts as vacation
_ARRIVAL_MULTIPLIER = {
    "morning": 0.0,  # Arrive at 9:00 → no vacation used
    "midday": 0.5,  # Arrive at 13:00 → half day
    "evening": 1.0,  # Arrive at 17:00 → full day
}

# Hours associated with each type (for single-day calculation)
_HOURS = {
    "morning": 9,
    "midday": 13,
    "evening": 17,
}


def count_vacation_days(
    start_date: date,
    end_date: date,
    holidays: set[date],
    departure_type: str = "morning",
    arrival_type: str = "evening",
) -> float:
    """Count vacation days consumed by a trip.

    Args:
        start_date: Trip start date (inclusive).
        end_date: Trip end date (inclusive).
        holidays: Set of public holiday dates to skip.
        departure_type: 'morning', 'midday', or 'evening'.
        arrival_type: 'morning', 'midday', or 'evening'.

    Returns:
        Number of vacation days (float, supports half-days).
    """
    if start_date > end_date:
        return 0.0

    # Single-day trip: calculate based on hours spent
    if start_date == end_date:
        if _is_non_working(start_date, holidays):
            return 0.0
        departure_hour = _HOURS.get(departure_type, 9)
        arrival_hour = _HOURS.get(arrival_type, 17)
        hours = arrival_hour - departure_hour
        return max(0.0, hours / 8.0)

    # Multi-day trip
    total = 0.0
    current = start_date
    while current <= end_date:
        if not _is_non_working(current, holidays):
            if current == start_date:
                total += _DEPARTURE_MULTIPLIER.get(departure_type, 1.0)
            elif current == end_date:
                total += _ARRIVAL_MULTIPLIER.get(arrival_type, 1.0)
            else:
                total += 1.0
        current += timedelta(days=1)

    return total


def _is_non_working(d: date, holidays: set[date]) -> bool:
    """Check if a date is a weekend or public holiday."""
    return d.weekday() >= 5 or d in holidays
