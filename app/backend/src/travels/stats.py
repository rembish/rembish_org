"""Public travel statistics endpoints."""

from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TCCDestination, Trip, TripDestination, Visit

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


def get_trip_days(trip: Trip) -> int:
    """Calculate trip duration in days."""
    start = trip.start_date
    end = trip.end_date or start
    return (end - start).days + 1


def get_trip_year(trip: Trip) -> int:
    """Get the primary year for a trip (start year)."""
    return trip.start_date.year


def get_trip_month(trip: Trip) -> int:
    """Get the primary month for a trip (start month)."""
    return trip.start_date.month


@router.get("/stats", response_model=TravelStatsResponse)
def get_travel_stats(db: Session = Depends(get_db)) -> TravelStatsResponse:
    """Get public travel statistics grouped by year."""

    # Get all trips
    trips = db.query(Trip).order_by(Trip.start_date).all()

    # Get all first visits (from visits table)
    first_visits = db.query(Visit).filter(Visit.first_visit_date.isnot(None)).all()
    first_visit_dates = {v.tcc_destination_id: v.first_visit_date for v in first_visits}

    # Get TCC destinations with their UN country info
    tcc_destinations = db.query(TCCDestination).all()
    tcc_info: dict[int, tuple[str, str | None]] = {}  # tcc_id -> (name, iso_code)
    for tcc in tcc_destinations:
        # Use TCC's own iso_alpha2 first (for non-UN territories), then fall back to UN country
        iso_code = tcc.iso_alpha2 or (tcc.un_country.iso_alpha2 if tcc.un_country else None)
        tcc_info[tcc.id] = (tcc.name, iso_code)

    # Get TCC destination IDs for each trip
    trip_destinations = db.query(TripDestination).all()
    trip_to_tccs = defaultdict(set)
    for td in trip_destinations:
        trip_to_tccs[td.trip_id].add(td.tcc_destination_id)

    # Build year -> month -> stats
    year_data: dict[int, dict] = defaultdict(
        lambda: {
            "trips": [],
            "months": defaultdict(lambda: {"trips": [], "tccs": set()}),
        }
    )

    # Track first visits by year/month
    tcc_first_visit_year: dict[int, int] = {}  # tcc_id -> year of first visit
    tcc_first_visit_month: dict[int, tuple[int, int]] = {}  # tcc_id -> (year, month)

    for tcc_id, visit_date in first_visit_dates.items():
        if visit_date:
            tcc_first_visit_year[tcc_id] = visit_date.year
            tcc_first_visit_month[tcc_id] = (visit_date.year, visit_date.month)

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

    for year in sorted(year_data.keys()):
        data = year_data[year]
        year_trips = data["trips"]

        # Calculate year stats
        year_days = sum(get_trip_days(t) for t in year_trips)
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

            month_days = sum(get_trip_days(t) for t in month_trips)

            # Countries visited this month
            month_countries = []
            for tcc_id in month_tccs:
                if tcc_id in tcc_info:
                    name, iso_code = tcc_info[tcc_id]
                    is_new = tcc_first_visit_month.get(tcc_id) == (year, month)
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

            month_stats.append(
                MonthStats(
                    month=month,
                    trips_count=len(month_trips),
                    days=month_days,
                    new_countries=month_new,
                    countries=month_countries,
                    event=event,
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
        "days": sum(get_trip_days(t) for t in trips),
        "countries": len(all_visited_ever),
        "years": len(year_data),
    }

    return TravelStatsResponse(
        years=sorted(years_stats, key=lambda y: y.year, reverse=True),
        totals=totals,
    )
