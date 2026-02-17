import logging
from datetime import date
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user
from ..config import settings
from ..database import get_db
from ..models import Airport, Flight, Trip, User
from .models import (
    AirportData,
    FlightCreateRequest,
    FlightData,
    FlightLookupLeg,
    FlightLookupResponse,
    FlightsResponse,
)

log = logging.getLogger(__name__)

router = APIRouter()


def _upsert_airport(
    db: Session,
    iata_code: str,
    name: str | None = None,
    city: str | None = None,
    country_code: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> Airport:
    """Find or create an airport by IATA code. Enriches existing records with new data."""
    iata = iata_code.upper().strip()
    airport = db.query(Airport).filter(Airport.iata_code == iata).first()
    if airport:
        # Enrich with richer data from API if we have it
        if name and not airport.name:
            airport.name = name
        if city and not airport.city:
            airport.city = city
        if country_code and not airport.country_code:
            airport.country_code = country_code
        if latitude is not None and airport.latitude is None:
            airport.latitude = latitude
        if longitude is not None and airport.longitude is None:
            airport.longitude = longitude
        if timezone and not airport.timezone:
            airport.timezone = timezone
    else:
        airport = Airport(
            iata_code=iata,
            name=name,
            city=city,
            country_code=country_code,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )
        db.add(airport)
        db.flush()
    return airport


def _airport_to_data(airport: Airport) -> AirportData:
    return AirportData(
        id=airport.id,
        iata_code=airport.iata_code,
        name=airport.name,
        city=airport.city,
        country_code=airport.country_code,
    )


def _flight_to_data(flight: Flight) -> FlightData:
    return FlightData(
        id=flight.id,
        trip_id=flight.trip_id,
        flight_date=flight.flight_date.isoformat(),
        flight_number=flight.flight_number,
        airline_name=flight.airline_name,
        departure_airport=_airport_to_data(flight.departure_airport),
        arrival_airport=_airport_to_data(flight.arrival_airport),
        departure_time=flight.departure_time,
        arrival_time=flight.arrival_time,
        arrival_date=flight.arrival_date.isoformat() if flight.arrival_date else None,
        terminal=flight.terminal,
        arrival_terminal=flight.arrival_terminal,
        gate=flight.gate,
        aircraft_type=flight.aircraft_type,
        seat=flight.seat,
        booking_reference=flight.booking_reference,
        notes=flight.notes,
    )


def _parse_time(iso_str: str | None) -> str | None:
    """Extract HH:MM from a datetime string.

    Handles both ISO format ('2026-01-16T19:40+01:00')
    and AeroDataBox format ('2026-01-16 19:40+01:00').
    """
    if not iso_str:
        return None
    try:
        # Already HH:MM
        if len(iso_str) == 5 and ":" in iso_str:
            return iso_str
        # Split on T or space to get the time part
        for sep in ("T", " "):
            if sep in iso_str:
                time_part = iso_str.split(sep, 1)[1]
                return time_part[:5]
    except (IndexError, ValueError):
        pass
    return None


def _parse_date_from_datetime(iso_str: str | None) -> str | None:
    """Extract YYYY-MM-DD from a datetime string like '2026-01-16 19:40+01:00'."""
    if not iso_str:
        return None
    try:
        return iso_str[:10]
    except (IndexError, ValueError):
        return None


@router.get("/flights/lookup", response_model=FlightLookupResponse)
def lookup_flight(
    flight_number: str = Query(..., min_length=2),
    date: str = Query(..., description="YYYY-MM-DD"),
    admin: Annotated[User, Depends(get_admin_user)] = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> FlightLookupResponse:
    """Look up flight legs from AeroDataBox API. Returns 501 if API key not configured."""
    if not settings.aerodatabox_api_key:
        raise HTTPException(status_code=501, detail="Flight lookup not configured")

    fn = flight_number.upper().strip()
    try:
        resp = httpx.get(
            f"https://aerodatabox.p.rapidapi.com/flights/number/{fn}/{date}",
            headers={
                "X-RapidAPI-Key": settings.aerodatabox_api_key,
                "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
            },
            timeout=10.0,
        )
        if resp.status_code == 204:
            return FlightLookupResponse(legs=[], error="No flight data found")
        if resp.status_code != 200:
            log.warning("AeroDataBox returned %d for %s/%s", resp.status_code, fn, date)
            return FlightLookupResponse(legs=[], error=f"API error ({resp.status_code})")

        data = resp.json()
        legs: list[FlightLookupLeg] = []

        # API returns a list of flight legs
        items = data if isinstance(data, list) else [data]
        for item in items:
            dep = item.get("departure", {})
            arr = item.get("arrival", {})
            dep_airport = dep.get("airport", {})
            arr_airport = arr.get("airport", {})
            aircraft = item.get("aircraft", {})

            dep_iata = dep_airport.get("iata", "")
            arr_iata = arr_airport.get("iata", "")
            if not dep_iata or not arr_iata:
                continue

            # Upsert airports from API data (including coordinates and timezone)
            dep_loc = dep_airport.get("location", {})
            arr_loc = arr_airport.get("location", {})
            _upsert_airport(
                db,
                dep_iata,
                name=dep_airport.get("name"),
                city=dep_airport.get("municipalityName"),
                country_code=dep_airport.get("countryCode"),
                latitude=dep_loc.get("lat"),
                longitude=dep_loc.get("lon"),
                timezone=dep_airport.get("timeZone"),
            )
            _upsert_airport(
                db,
                arr_iata,
                name=arr_airport.get("name"),
                city=arr_airport.get("municipalityName"),
                country_code=arr_airport.get("countryCode"),
                latitude=arr_loc.get("lat"),
                longitude=arr_loc.get("lon"),
                timezone=arr_airport.get("timeZone"),
            )

            dep_local = dep.get("scheduledTime", {}).get("local")
            arr_local = arr.get("scheduledTime", {}).get("local")
            dep_date_str = _parse_date_from_datetime(dep_local)
            arr_date_str = _parse_date_from_datetime(arr_local)

            legs.append(
                FlightLookupLeg(
                    flight_number=fn,
                    airline_name=item.get("airline", {}).get("name"),
                    departure_iata=dep_iata,
                    departure_name=dep_airport.get("name"),
                    arrival_iata=arr_iata,
                    arrival_name=arr_airport.get("name"),
                    departure_time=_parse_time(dep_local),
                    arrival_time=_parse_time(arr_local),
                    departure_date=dep_date_str,
                    arrival_date=arr_date_str if arr_date_str != dep_date_str else None,
                    terminal=dep.get("terminal"),
                    arrival_terminal=arr.get("terminal"),
                    aircraft_type=aircraft.get("model"),
                )
            )

        db.commit()
        return FlightLookupResponse(legs=legs)
    except httpx.HTTPError as e:
        log.warning("AeroDataBox request failed: %s", e)
        return FlightLookupResponse(legs=[], error="API request failed")


@router.get("/trips/{trip_id}/flights", response_model=FlightsResponse)
def get_trip_flights(
    trip_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> FlightsResponse:
    """Get all flights for a trip, ordered by date and departure time."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    flights = (
        db.query(Flight)
        .filter(Flight.trip_id == trip_id)
        .options(
            joinedload(Flight.departure_airport),
            joinedload(Flight.arrival_airport),
        )
        .order_by(Flight.flight_date, Flight.departure_time)
        .all()
    )

    # Self-heal flights_count if it drifted from actual flight records
    actual_count = len(flights) if flights else None
    if trip.flights_count != actual_count:
        trip.flights_count = actual_count
        db.commit()

    return FlightsResponse(flights=[_flight_to_data(f) for f in flights])


@router.get("/flights/dates")
def get_flight_dates(
    year: int = Query(...),
    admin: Annotated[User, Depends(get_admin_user)] = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> dict[str, list[str]]:
    """Return all flight dates for a given year, keyed by ISO date string."""
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    rows = (
        db.query(Flight.flight_date)
        .filter(Flight.flight_date >= start, Flight.flight_date <= end)
        .distinct()
        .all()
    )
    return {"dates": [r[0].isoformat() for r in rows]}


@router.post("/trips/{trip_id}/flights", response_model=FlightData)
def create_flight(
    trip_id: int,
    request: FlightCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> FlightData:
    """Create a flight for a trip. Upserts airports by IATA code."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    dep_airport = _upsert_airport(db, request.departure_iata)
    arr_airport = _upsert_airport(db, request.arrival_iata)

    flight = Flight(
        trip_id=trip_id,
        flight_date=date.fromisoformat(request.flight_date),
        flight_number=request.flight_number.upper().strip(),
        airline_name=request.airline_name,
        departure_airport_id=dep_airport.id,
        arrival_airport_id=arr_airport.id,
        departure_time=request.departure_time,
        arrival_time=request.arrival_time,
        arrival_date=date.fromisoformat(request.arrival_date) if request.arrival_date else None,
        terminal=request.terminal,
        arrival_terminal=request.arrival_terminal,
        gate=request.gate,
        aircraft_type=request.aircraft_type,
        seat=request.seat,
        booking_reference=request.booking_reference,
        notes=request.notes,
    )
    db.add(flight)
    db.flush()

    # Update trip flights_count
    trip.flights_count = db.query(Flight).filter(Flight.trip_id == trip_id).count()

    db.commit()
    db.refresh(flight)

    # Reload with relationships
    loaded = (
        db.query(Flight)
        .options(
            joinedload(Flight.departure_airport),
            joinedload(Flight.arrival_airport),
        )
        .filter(Flight.id == flight.id)
        .first()
    )
    assert loaded is not None
    return _flight_to_data(loaded)


@router.delete("/flights/{flight_id}", status_code=204)
def delete_flight(
    flight_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a single flight and update trip flights_count."""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    trip_id = flight.trip_id
    db.delete(flight)
    db.flush()

    # Update trip flights_count
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip:
        remaining = db.query(Flight).filter(Flight.trip_id == trip_id).count()
        trip.flights_count = remaining if remaining > 0 else None

    db.commit()
