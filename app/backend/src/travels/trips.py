import logging
from datetime import date
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user, get_trips_viewer
from ..database import get_db
from ..models import (
    TCCDestination,
    Trip,
    TripCity,
    TripDestination,
    TripParticipant,
    User,
    Visit,
)
from .models import (
    HolidaysResponse,
    PublicHoliday,
    TCCDestinationOption,
    TCCDestinationOptionsResponse,
    TripCityData,
    TripCityInput,
    TripCreateRequest,
    TripData,
    TripDestinationData,
    TripDestinationInput,
    TripParticipantData,
    TripsResponse,
    TripUpdateRequest,
    UserOption,
    UserOptionsResponse,
    VacationSummary,
)

# Re-export for backward compatibility with tests
from .trips_country_info import (  # noqa: F401
    _compute_timezone_offset,
    _get_health_requirements,
    _needs_adapter,
    _vaccine_matches,
)
from .trips_country_info import router as country_info_router
from .trips_external import (
    _currency_cache,
    _fetch_currency_rates,
    _fetch_frankfurter,
    _fetch_holidays_for_country,
    _fetch_holidays_raw,
    _fetch_open_er,
    _fetch_sunrise_sunset,
    _fetch_weather,
    _get_currency_name,
    _holidays_cache,
    _sunrise_cache,
    _weather_cache,
)
from .trips_nominatim import _search_nominatim
from .trips_nominatim import router as nominatim_router
from .vacation import ANNUAL_LEAVE_DAYS, count_vacation_days

log = logging.getLogger(__name__)

router = APIRouter()
router.include_router(country_info_router)
router.include_router(nominatim_router)


@router.get("/trips", response_model=TripsResponse)
def get_trips(
    admin: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> TripsResponse:
    """Get all trips (admin/viewer)."""
    trips = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination),
            joinedload(Trip.participants).joinedload(TripParticipant.user),
            joinedload(Trip.cities).joinedload(TripCity.city),
        )
        .order_by(Trip.start_date.desc())
        .all()
    )

    trips_data = [_trip_to_data(trip) for trip in trips]

    return TripsResponse(trips=trips_data, total=len(trips_data))


@router.get("/tcc-options", response_model=TCCDestinationOptionsResponse)
def get_tcc_options(
    admin: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> TCCDestinationOptionsResponse:
    """Get all TCC destinations for selector (admin/viewer)."""
    destinations = (
        db.query(TCCDestination)
        .options(joinedload(TCCDestination.un_country))
        .order_by(TCCDestination.tcc_region, TCCDestination.name)
        .all()
    )
    return TCCDestinationOptionsResponse(
        destinations=[
            TCCDestinationOption(
                id=d.id,
                name=d.name,
                region=d.tcc_region,
                country_code=d.iso_alpha2 or (d.un_country.iso_alpha2 if d.un_country else None),
            )
            for d in destinations
        ]
    )


@router.get("/users-options", response_model=UserOptionsResponse)
def get_users_options(
    admin: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> UserOptionsResponse:
    """Get all users for participant selector (admin/viewer). Excludes the admin (owner)."""
    users = db.query(User).filter(User.id != admin.id).order_by(User.name).all()
    return UserOptionsResponse(
        users=[
            UserOption(id=u.id, name=u.name, nickname=u.nickname, picture=u.picture) for u in users
        ]
    )


def _update_visits_for_trip(db: Session, trip: Trip) -> None:
    """Create/update Visit records when trip adds new destinations."""
    # Use end_date (trip completion) or start_date for single-day trips
    visit_date = trip.end_date or trip.start_date

    for trip_dest in trip.destinations:
        visit = (
            db.query(Visit).filter(Visit.tcc_destination_id == trip_dest.tcc_destination_id).first()
        )

        if visit is None:
            # New destination - create Visit
            db.add(
                Visit(
                    tcc_destination_id=trip_dest.tcc_destination_id,
                    first_visit_date=visit_date,
                )
            )
        elif visit.first_visit_date is None or visit_date < visit.first_visit_date:
            # Earlier visit found - update
            visit.first_visit_date = visit_date


def _recalculate_visit(db: Session, tcc_destination_id: int) -> None:
    """Find earliest trip visiting this destination and update Visit.

    Only updates first_visit_date if trip date is earlier than existing.
    Never clears existing dates (preserves check-in data).
    """
    earliest_trip = (
        db.query(Trip)
        .join(TripDestination)
        .filter(TripDestination.tcc_destination_id == tcc_destination_id)
        .order_by(Trip.start_date)
        .first()
    )

    visit = db.query(Visit).filter(Visit.tcc_destination_id == tcc_destination_id).first()

    if earliest_trip:
        # Use end_date (trip completion) or start_date for single-day trips
        visit_date = earliest_trip.end_date or earliest_trip.start_date
        if visit:
            # Only update if trip date is earlier (preserve check-in dates)
            if visit.first_visit_date is None or visit_date < visit.first_visit_date:
                visit.first_visit_date = visit_date
        else:
            db.add(Visit(tcc_destination_id=tcc_destination_id, first_visit_date=visit_date))
    # If no trips, don't clear existing visit date (may have been set by check-in)


def _trip_to_data(trip: Trip) -> TripData:
    """Convert Trip ORM object to TripData response."""
    return TripData(
        id=trip.id,
        start_date=trip.start_date.isoformat(),
        end_date=trip.end_date.isoformat() if trip.end_date else None,
        trip_type=trip.trip_type,
        flights_count=trip.flights_count,
        working_days=trip.working_days,
        rental_car=trip.rental_car,
        description=trip.description,
        departure_type=trip.departure_type,
        arrival_type=trip.arrival_type,
        destinations=[
            TripDestinationData(
                name=td.tcc_destination.name,
                is_partial=td.is_partial,
            )
            for td in trip.destinations
        ],
        cities=[
            TripCityData(
                name=city.name,
                is_partial=city.is_partial,
                country_code=city.city.country_code if city.city else None,
            )
            for city in sorted(trip.cities, key=lambda c: c.order)
        ],
        participants=[
            TripParticipantData(
                id=tp.user.id,
                name=tp.user.name,
                nickname=tp.user.nickname,
                picture=tp.user.picture,
            )
            for tp in trip.participants
        ],
        other_participants_count=trip.other_participants_count,
    )


@router.get("/trips/{trip_id}", response_model=TripData)
def get_trip(
    trip_id: int,
    admin: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> TripData:
    """Get a single trip by ID (admin/viewer)."""
    trip = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination),
            joinedload(Trip.participants).joinedload(TripParticipant.user),
            joinedload(Trip.cities).joinedload(TripCity.city),
        )
        .filter(Trip.id == trip_id)
        .first()
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return _trip_to_data(trip)


def _parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    return date.fromisoformat(date_str)


def _create_trip_relations(
    db: Session,
    trip: Trip,
    destinations: list[TripDestinationInput],
    cities: list[TripCityInput],
    participant_ids: list[int],
) -> None:
    """Create trip destinations, cities, and participants."""
    # Batch-validate destinations
    if destinations:
        dest_ids = [d.tcc_destination_id for d in destinations]
        valid_dests = {
            d.id for d in db.query(TCCDestination.id).filter(TCCDestination.id.in_(dest_ids)).all()
        }
        dest_partial = {d.tcc_destination_id: d.is_partial for d in destinations}
        for dest_id in dest_ids:
            if dest_id in valid_dests:
                trip.destinations.append(
                    TripDestination(
                        tcc_destination_id=dest_id,
                        is_partial=dest_partial[dest_id],
                    )
                )

    # Add cities
    for i, city_input in enumerate(cities):
        trip.cities.append(
            TripCity(
                name=city_input.name,
                is_partial=city_input.is_partial,
                order=i,
            )
        )

    # Batch-validate participants (dedupe to prevent unique constraint violations)
    unique_participant_ids = list(dict.fromkeys(participant_ids))
    if unique_participant_ids:
        valid_users = {
            u.id for u in db.query(User.id).filter(User.id.in_(unique_participant_ids)).all()
        }
        for user_id in unique_participant_ids:
            if user_id in valid_users:
                trip.participants.append(TripParticipant(user_id=user_id))


@router.post("/trips", response_model=TripData)
def create_trip(
    request: TripCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> TripData:
    """Create a new trip (admin only)."""
    trip = Trip(
        start_date=_parse_date(request.start_date),
        end_date=_parse_date(request.end_date) if request.end_date else None,
        trip_type=request.trip_type,
        flights_count=request.flights_count,
        working_days=request.working_days,
        rental_car=request.rental_car,
        description=request.description,
        departure_type=request.departure_type,
        arrival_type=request.arrival_type,
        other_participants_count=request.other_participants_count,
    )

    db.add(trip)
    db.flush()  # Get trip.id

    _create_trip_relations(db, trip, request.destinations, request.cities, request.participant_ids)

    db.flush()

    # Update visit records
    _update_visits_for_trip(db, trip)

    db.commit()

    # Reload with relationships
    db.refresh(trip)
    loaded_trip = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination),
            joinedload(Trip.participants).joinedload(TripParticipant.user),
            joinedload(Trip.cities).joinedload(TripCity.city),
        )
        .filter(Trip.id == trip.id)
        .first()
    )
    assert loaded_trip is not None

    return _trip_to_data(loaded_trip)


@router.put("/trips/{trip_id}", response_model=TripData)
def update_trip(
    trip_id: int,
    request: TripUpdateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> TripData:
    """Update a trip (admin only)."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Track old destination IDs for visit recalculation
    old_destination_ids = {td.tcc_destination_id for td in trip.destinations}

    # Update basic fields if provided
    if request.start_date is not None:
        trip.start_date = _parse_date(request.start_date)
    if request.end_date is not None:
        trip.end_date = _parse_date(request.end_date) if request.end_date else None
    if request.trip_type is not None:
        trip.trip_type = request.trip_type
    if request.flights_count is not None:
        trip.flights_count = request.flights_count
    if request.working_days is not None:
        trip.working_days = request.working_days
    if request.rental_car is not None:
        trip.rental_car = request.rental_car
    if request.description is not None:
        trip.description = request.description
    if request.other_participants_count is not None:
        trip.other_participants_count = request.other_participants_count
    if request.departure_type is not None:
        trip.departure_type = request.departure_type
    if request.arrival_type is not None:
        trip.arrival_type = request.arrival_type

    # Update destinations if provided
    if request.destinations is not None:
        # Batch-validate destination IDs
        dest_ids = [d.tcc_destination_id for d in request.destinations]
        valid_dests = (
            {
                d.id
                for d in db.query(TCCDestination.id).filter(TCCDestination.id.in_(dest_ids)).all()
            }
            if dest_ids
            else set()
        )
        # Clear existing and recreate
        trip.destinations.clear()
        for dest_input in request.destinations:
            if dest_input.tcc_destination_id in valid_dests:
                trip.destinations.append(
                    TripDestination(
                        tcc_destination_id=dest_input.tcc_destination_id,
                        is_partial=dest_input.is_partial,
                    )
                )

    # Update cities if provided
    if request.cities is not None:
        # Preserve city_id links set by location check-in
        old_city_ids = {tc.name: tc.city_id for tc in trip.cities if tc.city_id}
        trip.cities.clear()
        for i, city_input in enumerate(request.cities):
            trip.cities.append(
                TripCity(
                    name=city_input.name,
                    is_partial=city_input.is_partial,
                    order=i,
                    city_id=old_city_ids.get(city_input.name),
                )
            )

    # Update participants if changed (dedupe to prevent unique constraint violations)
    if request.participant_ids is not None:
        unique_participant_ids = list(dict.fromkeys(request.participant_ids))
        existing_ids = sorted(p.user_id for p in trip.participants)
        requested_ids = sorted(unique_participant_ids)
        if existing_ids != requested_ids:
            valid_users = (
                {u.id for u in db.query(User.id).filter(User.id.in_(unique_participant_ids)).all()}
                if unique_participant_ids
                else set()
            )
            trip.participants.clear()
            db.flush()
            for user_id in unique_participant_ids:
                if user_id in valid_users:
                    trip.participants.append(TripParticipant(user_id=user_id))

    db.flush()

    # Get new destination IDs
    new_destination_ids = {td.tcc_destination_id for td in trip.destinations}

    # Recalculate visits for all affected destinations
    affected_ids = old_destination_ids | new_destination_ids
    for dest_id in affected_ids:
        _recalculate_visit(db, dest_id)

    db.commit()

    # Reload with relationships
    loaded_trip = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination),
            joinedload(Trip.participants).joinedload(TripParticipant.user),
            joinedload(Trip.cities).joinedload(TripCity.city),
        )
        .filter(Trip.id == trip.id)
        .first()
    )
    assert loaded_trip is not None

    return _trip_to_data(loaded_trip)


@router.delete("/trips/{trip_id}")
def delete_trip(
    trip_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> dict:
    """Delete a trip (admin only). Visit records are kept for historical tracking."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Track destination IDs for visit recalculation
    destination_ids = {td.tcc_destination_id for td in trip.destinations}

    # Delete the trip (cascades to trip_destinations, trip_cities, trip_participants)
    db.delete(trip)
    db.flush()

    # Recalculate visits for affected destinations
    for dest_id in destination_ids:
        _recalculate_visit(db, dest_id)

    db.commit()

    return {"message": "Trip deleted"}


@router.get("/vacation-summary", response_model=VacationSummary)
def get_vacation_summary(
    admin: Annotated[User, Depends(get_trips_viewer)],
    year: int = Query(...),
    db: Session = Depends(get_db),
) -> VacationSummary:
    """Calculate vacation day balance for a year (admin only).

    Only 'regular' trips consume vacation days.
    Uses CZ public holidays for working day calculation.
    """
    today = date.today()
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    # Fetch all regular trips that overlap with the year
    trips = (
        db.query(Trip)
        .filter(
            Trip.trip_type == "regular",
            Trip.start_date <= year_end,
        )
        .all()
    )

    # Filter to trips that actually overlap the year (end_date >= year_start)
    overlapping = [t for t in trips if (t.end_date or t.start_date) >= year_start]

    # Fetch CZ holidays for the year
    raw_holidays = _fetch_holidays_raw(year, "CZ")
    holiday_dates: set[date] = set()
    for h in raw_holidays:
        try:
            holiday_dates.add(date.fromisoformat(h["date"]))
        except (KeyError, ValueError):
            pass

    used_days = 0.0
    planned_days = 0.0

    for trip in overlapping:
        trip_start = trip.start_date
        trip_end = trip.end_date or trip.start_date

        # Clamp trip dates to year boundaries
        clamped_start = max(trip_start, year_start)
        clamped_end = min(trip_end, year_end)

        # Determine departure/arrival types for clamped dates
        dep_type = trip.departure_type if clamped_start == trip_start else "morning"
        arr_type = trip.arrival_type if clamped_end == trip_end else "evening"

        days = count_vacation_days(clamped_start, clamped_end, holiday_dates, dep_type, arr_type)

        if trip_end < today:
            used_days += days
        else:
            planned_days += days

    remaining = ANNUAL_LEAVE_DAYS - used_days - planned_days

    return VacationSummary(
        annual_days=ANNUAL_LEAVE_DAYS,
        used_days=round(used_days, 1),
        planned_days=round(planned_days, 1),
        remaining_days=round(remaining, 1),
    )


@router.get("/holidays/{year}/{country_code}", response_model=HolidaysResponse)
def get_holidays(
    year: int,
    country_code: str,
    admin: Annotated[User, Depends(get_trips_viewer)],
) -> HolidaysResponse:
    """Get public holidays for a year/country from Nager.Date API (admin only).

    Uses in-memory cache with 24h TTL.
    """
    country_code = country_code.upper()
    cache_key = (year, country_code)

    # Check cache
    cached_holidays = _holidays_cache.get(cache_key)
    if cached_holidays is not None:
        return HolidaysResponse(
            holidays=[
                PublicHoliday(
                    date=h["date"],
                    name=h["name"],
                    local_name=h.get("localName"),
                )
                for h in cached_holidays
            ]
        )

    # Fetch from Nager.Date API
    try:
        response = httpx.get(
            f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}",
            timeout=10.0,
        )
        if response.status_code in (204, 404):
            _holidays_cache[cache_key] = []
            return HolidaysResponse(holidays=[])

        response.raise_for_status()
        data = response.json()
        _holidays_cache[cache_key] = data

        return HolidaysResponse(
            holidays=[
                PublicHoliday(
                    date=h["date"],
                    name=h["name"],
                    local_name=h.get("localName"),
                )
                for h in data
            ]
        )
    except Exception:
        return HolidaysResponse(holidays=[])


# Keep these names available for backward compatibility (used in re-exports and tests).
# The actual implementations live in trips_external, trips_country_info, trips_nominatim.
__all__ = [
    "_currency_cache",
    "_fetch_currency_rates",
    "_fetch_frankfurter",
    "_fetch_holidays_for_country",
    "_fetch_holidays_raw",
    "_fetch_open_er",
    "_fetch_sunrise_sunset",
    "_fetch_weather",
    "_get_currency_name",
    "_holidays_cache",
    "_sunrise_cache",
    "_weather_cache",
    "_search_nominatim",
    "_compute_timezone_offset",
    "_get_health_requirements",
    "_needs_adapter",
    "_vaccine_matches",
]
