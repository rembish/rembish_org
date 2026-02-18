"""Public travel statistics endpoints."""

import re
from collections import defaultdict
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user_optional
from ..database import get_db
from ..models import Airport, Flight, TCCDestination, Trip, TripDestination, User, Visit
from .models import FlightStatsResponse, RankedItem, YearFlightCount

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

    # Flight aggregates (per project pitfall: use Python set union, not .union().subquery())
    total_flights = (
        db.query(func.count(Flight.id)).filter(Flight.flight_date <= today).scalar() or 0
    )
    planned_flights = (
        db.query(func.count(Flight.id)).filter(Flight.flight_date > today).scalar() or 0
    )
    dep_set = {
        r[0]
        for r in db.query(Flight.departure_airport_id).filter(Flight.flight_date <= today).all()
    }
    arr_set = {
        r[0] for r in db.query(Flight.arrival_airport_id).filter(Flight.flight_date <= today).all()
    }
    total_airports = len(dep_set | arr_set)
    total_airlines = (
        db.query(func.count(func.distinct(Flight.airline_name)))
        .filter(Flight.flight_date <= today, Flight.airline_name.isnot(None))
        .scalar()
        or 0
    )

    # Calculate totals
    totals = {
        "trips": len(trips),
        "planned_trips": planned_trips_count,
        "days": sum(get_trip_days(t, cap_date) for t in trips),
        "countries": len(all_visited_ever),
        "years": len(year_data),
        "total_flights": total_flights,
        "planned_flights": planned_flights,
        "total_airports": total_airports,
        "total_airlines": total_airlines,
    }

    return TravelStatsResponse(
        years=sorted(years_stats, key=lambda y: y.year, reverse=True),
        totals=totals,
    )


def _aircraft_family(aircraft_type: str) -> str:
    """Group aircraft type into family. E.g. 'Airbus A321neo' -> 'Airbus A320 family'."""
    t = aircraft_type.strip()
    low = t.lower()

    # Airbus A3xx family grouping
    if low.startswith("airbus a3"):
        # A318/A319/A320/A321 -> A320 family
        m = re.match(r"airbus\s+a3(1[89]|2[01])", low)
        if m:
            return "Airbus A320 family"
        # A330/A340 -> A330/A340
        m = re.match(r"airbus\s+a3([34])\d", low)
        if m:
            base = "A3" + m.group(1) + "0"
            return f"Airbus {base}"
        # A350, A380 etc.
        m = re.match(r"airbus\s+(a\d{3})", low)
        if m:
            return f"Airbus {m.group(1).upper()}"

    # Boeing 7x7 grouping
    if low.startswith("boeing"):
        m = re.match(r"boeing\s+(\d{3})", low)
        if m:
            return f"Boeing {m.group(1)}"

    # ATR family
    if low.startswith("atr"):
        m = re.match(r"atr\s*(\d{2})", low)
        if m:
            return f"ATR {m.group(1)}"
        return "ATR"

    # Embraer
    if low.startswith("embraer") or low.startswith("erj"):
        m = re.match(r"(?:embraer|erj)\s*[-\s]?(\d{3})", low)
        if m:
            model = int(m.group(1))
            if 170 <= model <= 195:
                return "Embraer E-Jet"
            return f"Embraer {m.group(1)}"
        return "Embraer"

    # Bombardier / CRJ / Dash
    if "crj" in low or "canadair" in low:
        return "Bombardier CRJ"
    if "dash" in low or "dhc" in low or "de havilland" in low:
        return "De Havilland Dash"

    # Fallback: return as-is
    return t


@router.get("/flight-stats", response_model=FlightStatsResponse)
def get_flight_stats(db: Session = Depends(get_db)) -> FlightStatsResponse:
    """Get detailed flight statistics: top airlines, airports, routes, aircraft types."""

    today = date.today()

    flights = db.query(Flight).filter(Flight.flight_date <= today).all()

    # Build airport lookup (id -> Airport)
    airport_ids = set()
    for f in flights:
        airport_ids.add(f.departure_airport_id)
        airport_ids.add(f.arrival_airport_id)

    airports_by_id: dict[int, Airport] = {}
    if airport_ids:
        for a in db.query(Airport).filter(Airport.id.in_(airport_ids)).all():
            airports_by_id[a.id] = a

    # Single pass aggregation
    airline_counts: dict[str, int] = {}
    airport_counts: dict[int, int] = {}
    route_counts: dict[tuple[int, int], int] = {}
    aircraft_counts: dict[str, int] = {}  # family -> total count
    aircraft_variants: dict[str, dict[str, int]] = {}  # family -> {variant -> count}
    year_counts: dict[int, int] = {}

    for f in flights:
        # Airlines
        if f.airline_name:
            airline_counts[f.airline_name] = airline_counts.get(f.airline_name, 0) + 1

        # Airports (departures + arrivals)
        airport_counts[f.departure_airport_id] = airport_counts.get(f.departure_airport_id, 0) + 1
        airport_counts[f.arrival_airport_id] = airport_counts.get(f.arrival_airport_id, 0) + 1

        # Routes (normalize: smaller ID first)
        route_key = (
            min(f.departure_airport_id, f.arrival_airport_id),
            max(f.departure_airport_id, f.arrival_airport_id),
        )
        route_counts[route_key] = route_counts.get(route_key, 0) + 1

        # Aircraft types (grouped by family)
        if f.aircraft_type:
            family = _aircraft_family(f.aircraft_type)
            aircraft_counts[family] = aircraft_counts.get(family, 0) + 1
            variants = aircraft_variants.setdefault(family, {})
            variants[f.aircraft_type] = variants.get(f.aircraft_type, 0) + 1

        # Flights by year
        year = f.flight_date.year
        year_counts[year] = year_counts.get(year, 0) + 1

    # Build top lists
    top_airlines = sorted(airline_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    top_airports_raw = sorted(airport_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    top_routes_raw = sorted(route_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    aircraft_sorted = sorted(aircraft_counts.items(), key=lambda x: x[1], reverse=True)

    # Unique counts
    unique_airport_ids = set()
    for f in flights:
        unique_airport_ids.add(f.departure_airport_id)
        unique_airport_ids.add(f.arrival_airport_id)

    unique_airlines = {f.airline_name for f in flights if f.airline_name}
    unique_aircraft = {f.aircraft_type for f in flights if f.aircraft_type}

    # Format airports (name=IATA, extra=country_code|full_name for flag+tooltip)
    top_airports: list[RankedItem] = []
    for aid, count in top_airports_raw:
        ap = airports_by_id.get(aid)
        if ap:
            extra = f"{ap.country_code or ''}|{ap.name or ''}"
            top_airports.append(RankedItem(name=ap.iata_code, count=count, extra=extra))

    # Format routes
    top_routes: list[RankedItem] = []
    for (a_id, b_id), count in top_routes_raw:
        ap_a = airports_by_id.get(a_id)
        ap_b = airports_by_id.get(b_id)
        if ap_a and ap_b:
            label = f"{ap_a.iata_code} — {ap_b.iata_code}"
            top_routes.append(RankedItem(name=label, count=count))

    return FlightStatsResponse(
        total_flights=len(flights),
        total_airports=len(unique_airport_ids),
        total_airlines=len(unique_airlines),
        total_aircraft_types=len(unique_aircraft),
        top_airlines=[RankedItem(name=name, count=count) for name, count in top_airlines],
        top_airports=top_airports,
        top_routes=top_routes,
        aircraft_types=[
            RankedItem(
                name=name,
                count=count,
                extra=", ".join(
                    f"{v} ({c})" for v, c in sorted(aircraft_variants.get(name, {}).items())
                )
                if len(aircraft_variants.get(name, {})) > 1
                else None,
            )
            for name, count in aircraft_sorted
        ],
        flights_by_year=[
            YearFlightCount(year=y, count=c) for y, c in sorted(year_counts.items(), reverse=True)
        ],
    )
