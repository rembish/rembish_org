"""Public travel statistics endpoints."""

from collections import defaultdict
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user_optional
from ..database import get_db
from ..models import TCCDestination, Trip, TripDestination, User, Visit

router = APIRouter()


class MonthCountry(BaseModel):
    name: str
    iso_code: str | None  # For flag display
    is_new: bool  # First visit ever


class MonthStats(BaseModel):
    month: int  # 1-12
    trips_count: int
    days: int
    new_countries: int  # First-time TCC visits this month
    countries: list[MonthCountry]  # Countries visited this month
    event: str | None = None  # Special event: "birthday", "relocation"
    is_planned: bool = False  # True if this month contains only future trips
    has_planned_trips: bool = False  # True if month has any planned trips (for mixed styling)


class YearStats(BaseModel):
    year: int
    trips_count: int
    days: int
    countries_visited: int  # Unique TCC destinations visited
    new_countries: int  # First-time TCC visits
    work_trips: int
    flights: int
    months: list[MonthStats]


class TravelStatsResponse(BaseModel):
    years: list[YearStats]
    totals: dict  # Overall totals


def get_trip_days(trip: Trip, today: date | None = None) -> int:
    """Calculate trip duration in days. For ongoing trips, cap at today."""
    start = trip.start_date
    end = trip.end_date or start
    # For ongoing trips (started but not ended), only count days up to today
    if today and start <= today < end:
        end = today
    return (end - start).days + 1


def get_trip_year(trip: Trip) -> int:
    """Get the primary year for a trip (start year)."""
    return trip.start_date.year


def get_trip_month(trip: Trip) -> int:
    """Get the primary month for a trip (start month)."""
    return trip.start_date.month


@router.get("/stats", response_model=TravelStatsResponse)
def get_travel_stats(
    db: Session = Depends(get_db),
    user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> TravelStatsResponse:
    """Get public travel statistics grouped by year."""

    today = date.today()

    # Single query for all trips, split in Python
    all_trips = db.query(Trip).order_by(Trip.start_date).all()
    started_trips = [t for t in all_trips if t.start_date <= today]
    future_trips = [t for t in all_trips if t.start_date > today]

    planned_trips_count = len(future_trips)

    # Include future trips if user is logged in
    planned_trip_ids: set[int] = set()
    if user:
        trips = started_trips + future_trips
        # Track which trip IDs are planned
        planned_trip_ids = {t.id for t in future_trips}
    else:
        trips = started_trips

    # Get TCC destinations with their UN country info (eager-load to avoid N+1)
    tcc_destinations = db.query(TCCDestination).options(joinedload(TCCDestination.un_country)).all()
    tcc_info: dict[int, tuple[str, str | None]] = {}  # tcc_id -> (name, iso_code)
    for tcc in tcc_destinations:
        # Use TCC's own iso_alpha2 first (for non-UN territories), then fall back to UN country
        iso_code = tcc.iso_alpha2 or (tcc.un_country.iso_alpha2 if tcc.un_country else None)
        tcc_info[tcc.id] = (tcc.name, iso_code)

    # Get TCC destination IDs for each trip
    # For anonymous users: only show checked-in destinations (first_visit_date <= today)
    # For logged-in users: show all destinations
    trip_destinations = db.query(TripDestination).all()
    trip_to_tccs = defaultdict(set)

    if user:
        # Logged-in: show all destinations
        for td in trip_destinations:
            trip_to_tccs[td.trip_id].add(td.tcc_destination_id)
    else:
        # Anonymous: only show visited destinations
        visited_tcc_ids = {
            v.tcc_destination_id
            for v in db.query(Visit).filter(Visit.first_visit_date <= today).all()
        }
        for td in trip_destinations:
            if td.tcc_destination_id in visited_tcc_ids:
                trip_to_tccs[td.trip_id].add(td.tcc_destination_id)

    # Build year -> month -> stats
    year_data: dict[int, dict] = defaultdict(
        lambda: {
            "trips": [],
            "months": defaultdict(lambda: {"trips": [], "tccs": set()}),
        }
    )

    # Track first trip to each destination (for "is_new" marking)
    # Since first_visit_date now uses trip end_date, we can't rely on month matching.
    # Instead, find the earliest trip to each destination.
    tcc_first_trip: dict[int, int] = {}  # tcc_id -> trip_id of first visit
    tcc_first_visit_year: dict[int, int] = {}  # tcc_id -> year of first visit (for yearly stats)

    # Sort trips by start_date to find first trip per destination
    sorted_trips = sorted(trips, key=lambda t: t.start_date)
    for trip in sorted_trips:
        for tcc_id in trip_to_tccs[trip.id]:
            if tcc_id not in tcc_first_trip:
                tcc_first_trip[tcc_id] = trip.id
                tcc_first_visit_year[tcc_id] = trip.start_date.year

    # Process trips
    for trip in trips:
        year = get_trip_year(trip)
        month = get_trip_month(trip)

        year_data[year]["trips"].append(trip)
        year_data[year]["months"][month]["trips"].append(trip)
        year_data[year]["months"][month]["tccs"].update(trip_to_tccs[trip.id])

    # Build response
    years_stats = []
    all_visited_ever: set[int] = set()

    # For anonymous users, cap ongoing trip days at today
    # For logged-in users, show full trip duration
    cap_date = None if user else today

    for year in sorted(year_data.keys()):
        data = year_data[year]
        year_trips = data["trips"]

        # Calculate year stats
        year_days = sum(get_trip_days(t, cap_date) for t in year_trips)
        year_work_trips = sum(1 for t in year_trips if t.trip_type == "work")
        year_flights = sum(t.flights_count or 0 for t in year_trips)

        # Unique TCC destinations visited this year
        year_tccs: set[int] = set()
        for trip in year_trips:
            year_tccs.update(trip_to_tccs[trip.id])

        # New countries this year (first visit was this year)
        year_new = sum(1 for tcc_id in year_tccs if tcc_first_visit_year.get(tcc_id) == year)

        # Monthly breakdown
        month_stats = []
        for month in range(1, 13):
            month_data = data["months"].get(month, {"trips": [], "tccs": set()})
            month_trips = month_data["trips"]
            month_tccs = month_data["tccs"]

            if not month_trips:
                continue

            month_days = sum(get_trip_days(t, cap_date) for t in month_trips)

            # Countries visited this month
            # Get trip IDs in this month to check for first visits
            month_trip_ids = {t.id for t in month_trips}

            month_countries = []
            for tcc_id in month_tccs:
                if tcc_id in tcc_info:
                    name, iso_code = tcc_info[tcc_id]
                    # Mark as "new" if the first trip to this destination is in this month
                    is_new = tcc_first_trip.get(tcc_id) in month_trip_ids
                    month_countries.append(
                        MonthCountry(
                            name=name,
                            iso_code=iso_code,
                            is_new=is_new,
                        )
                    )

            # Sort: new countries first, then alphabetically
            month_countries.sort(key=lambda c: (not c.is_new, c.name))

            # New countries this specific month
            month_new = sum(1 for c in month_countries if c.is_new)

            # Check for special events
            event = None
            if any(t.trip_type == "relocation" for t in month_trips):
                event = "relocation"

            # Check planned status for this month
            is_month_planned = all(t.id in planned_trip_ids for t in month_trips)
            has_any_planned = any(t.id in planned_trip_ids for t in month_trips)

            month_stats.append(
                MonthStats(
                    month=month,
                    trips_count=len(month_trips),
                    days=month_days,
                    new_countries=month_new,
                    countries=month_countries,
                    event=event,
                    is_planned=is_month_planned,
                    has_planned_trips=has_any_planned,
                )
            )

        years_stats.append(
            YearStats(
                year=year,
                trips_count=len(year_trips),
                days=year_days,
                countries_visited=len(year_tccs),
                new_countries=year_new,
                work_trips=year_work_trips,
                flights=year_flights,
                months=month_stats,
            )
        )

        all_visited_ever.update(year_tccs)

    # Add birthday entry (May 12, 1985 - Novosibirsk, Russia)
    birthday_year = YearStats(
        year=1985,
        trips_count=0,
        days=0,
        countries_visited=1,
        new_countries=1,
        work_trips=0,
        flights=0,
        months=[
            MonthStats(
                month=5,
                trips_count=0,
                days=0,
                new_countries=1,
                countries=[MonthCountry(name="Russia in Asia", iso_code="ru", is_new=True)],
                event="birthday",
            )
        ],
    )
    years_stats.append(birthday_year)

    # Calculate totals
    totals = {
        "trips": len(trips),
        "planned_trips": planned_trips_count,
        "days": sum(get_trip_days(t, cap_date) for t in trips),
        "countries": len(all_visited_ever),
        "years": len(year_data),
    }

    return TravelStatsResponse(
        years=sorted(years_stats, key=lambda y: y.year, reverse=True),
        totals=totals,
    )
