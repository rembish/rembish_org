import time
from datetime import date, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user
from ..database import get_db
from ..models import (
    City,
    TCCDestination,
    Trip,
    TripCity,
    TripDestination,
    TripParticipant,
    UNCountry,
    User,
    Visit,
)
from .models import (
    CitySearchResponse,
    CitySearchResult,
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
)

# Nominatim rate limiting - track last request time
_nominatim_last_request: float = 0.0
_NOMINATIM_COOLDOWN = 1.0  # seconds between requests

# Holidays cache: {(year, country_code): (holidays_list, timestamp)}
_holidays_cache: dict[tuple[int, str], tuple[list[dict], float]] = {}
_HOLIDAYS_CACHE_TTL = 86400  # 24 hours

router = APIRouter()


@router.get("/trips", response_model=TripsResponse)
def get_trips(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> TripsResponse:
    """Get all trips (admin only)."""
    trips = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination),
            joinedload(Trip.participants).joinedload(TripParticipant.user),
            joinedload(Trip.cities),
        )
        .order_by(Trip.start_date.desc())
        .all()
    )

    trips_data = [
        TripData(
            id=trip.id,
            start_date=trip.start_date.isoformat(),
            end_date=trip.end_date.isoformat() if trip.end_date else None,
            trip_type=trip.trip_type,
            flights_count=trip.flights_count,
            working_days=trip.working_days,
            rental_car=trip.rental_car,
            description=trip.description,
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
        for trip in trips
    ]

    return TripsResponse(trips=trips_data, total=len(trips_data))


@router.get("/tcc-options", response_model=TCCDestinationOptionsResponse)
def get_tcc_options(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> TCCDestinationOptionsResponse:
    """Get all TCC destinations for selector (admin only)."""
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
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> UserOptionsResponse:
    """Get all users for participant selector (admin only). Excludes the admin (owner)."""
    users = db.query(User).filter(User.id != admin.id).order_by(User.name).all()
    return UserOptionsResponse(
        users=[
            UserOption(id=u.id, name=u.name, nickname=u.nickname, picture=u.picture) for u in users
        ]
    )


def _search_nominatim(
    query: str,
    country_name: str | None = None,
    fallback_country_code: str | None = None,
) -> list[CitySearchResult]:
    """Search Nominatim with rate limiting. Returns empty list on error."""
    global _nominatim_last_request

    # Enforce cooldown
    elapsed = time.time() - _nominatim_last_request
    if elapsed < _NOMINATIM_COOLDOWN:
        time.sleep(_NOMINATIM_COOLDOWN - elapsed)

    # Use structured search for better results
    # Using 'country' parameter (name) instead of 'countrycodes' for complete address data
    params: dict[str, str | int] = {
        "city": query,
        "format": "json",
        "limit": 5,
        "addressdetails": 1,
    }
    if country_name:
        # Single country - use structured search with country name
        params["country"] = country_name

    try:
        _nominatim_last_request = time.time()
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers={
                "User-Agent": "rembish.org travel tracker (hobby project)",
                "Accept-Language": "en",
            },
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        seen_names = set()
        query_lower = query.lower()

        for item in data:
            address = item.get("address", {})
            item_name = item.get("name", "")

            # Get country info - use fallback if not in address
            country = address.get("country") or country_name
            country_code = address.get("country_code", "").upper() or fallback_country_code

            # Build city name - prefer actual city fields from address
            city_name = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
            )

            # If no city field, check if the item name is a valid city
            if not city_name:
                # Skip if name contains region keywords
                if any(
                    kw in item_name.lower()
                    for kw in (
                        "emirate",
                        "region",
                        "province",
                        "state",
                        "county",
                        "district",
                        "governorate",
                    )
                ):
                    continue
                # Accept if it matches the search query (user is explicitly searching for it)
                if query_lower in item_name.lower():
                    city_name = item_name
                else:
                    continue

            if not city_name:
                continue

            # Skip duplicates
            name_key = city_name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            results.append(
                CitySearchResult(
                    name=city_name,
                    country=country,
                    country_code=country_code,
                    display_name=f"{city_name}, {country}" if country else city_name,
                    lat=float(item.get("lat", 0)),
                    lng=float(item.get("lon", 0)),
                    source="nominatim",
                )
            )
        return results
    except Exception:
        return []


@router.get("/cities-search", response_model=CitySearchResponse)
def search_cities(
    q: str = Query(..., min_length=2),
    country_codes: str | None = Query(None, description="Comma-separated ISO alpha-2 codes"),
    admin: Annotated[User | None, Depends(get_admin_user)] = None,
    db: Session = Depends(get_db),
) -> CitySearchResponse:
    """Search cities - local DB first, then Nominatim (admin only)."""
    results: list[CitySearchResult] = []
    codes = [c.strip().upper() for c in country_codes.split(",")] if country_codes else None

    # Search local City table first
    local_query = db.query(City).filter(City.name.ilike(f"%{q}%"))
    if codes:
        # Filter by country_code (ISO alpha-2), case-insensitive
        local_query = local_query.filter(City.country_code.in_(codes))
    local_cities = local_query.limit(10).all()

    for city in local_cities:
        results.append(
            CitySearchResult(
                name=city.name,
                country=city.country,
                country_code=city.country_code,
                display_name=city.display_name or f"{city.name}, {city.country}"
                if city.country
                else city.name,
                lat=city.lat,
                lng=city.lng,
                source="local",
            )
        )

    # If few local results, search Nominatim
    if len(results) < 5:
        # Convert country codes to country names for Nominatim (better results with country param)
        country_name: str | None = None
        fallback_code: str | None = None
        if codes and len(codes) == 1:
            fallback_code = codes[0]
            un_country = db.query(UNCountry).filter(UNCountry.iso_alpha2 == codes[0]).first()
            if un_country:
                country_name = un_country.name
        nominatim_results = _search_nominatim(q, country_name, fallback_code)
        # Add only non-duplicate results
        local_names = {r.name.lower() for r in results}
        for nr in nominatim_results:
            if nr.name.lower() not in local_names:
                results.append(nr)
                # Cache to local DB - only if we have country_code (for flag display)
                if nr.lat and nr.lng and nr.country_code:
                    # Check for existing by name + country_code (more reliable than country name)
                    existing = (
                        db.query(City)
                        .filter(
                            City.name == nr.name,
                            City.country_code == nr.country_code,
                        )
                        .first()
                    )
                    if not existing:
                        db.add(
                            City(
                                name=nr.name,
                                country=nr.country,
                                country_code=nr.country_code,
                                display_name=nr.display_name,
                                lat=nr.lat,
                                lng=nr.lng,
                                geocoded_at=datetime.utcnow(),
                                confidence="nominatim",
                            )
                        )
        db.commit()

    return CitySearchResponse(results=results[:10])


def _update_visits_for_trip(db: Session, trip: Trip) -> None:
    """Create/update Visit records when trip adds new destinations."""
    first_of_month = trip.start_date.replace(day=1)

    for trip_dest in trip.destinations:
        visit = (
            db.query(Visit).filter(Visit.tcc_destination_id == trip_dest.tcc_destination_id).first()
        )

        if visit is None:
            # New destination - create Visit
            db.add(
                Visit(
                    tcc_destination_id=trip_dest.tcc_destination_id,
                    first_visit_date=first_of_month,
                )
            )
        elif visit.first_visit_date is None or first_of_month < visit.first_visit_date:
            # Earlier visit found - update
            visit.first_visit_date = first_of_month


def _recalculate_visit(db: Session, tcc_destination_id: int) -> None:
    """Find earliest trip visiting this destination and update Visit."""
    earliest_trip = (
        db.query(Trip)
        .join(TripDestination)
        .filter(TripDestination.tcc_destination_id == tcc_destination_id)
        .order_by(Trip.start_date)
        .first()
    )

    visit = db.query(Visit).filter(Visit.tcc_destination_id == tcc_destination_id).first()

    if earliest_trip:
        first_of_month = earliest_trip.start_date.replace(day=1)
        if visit:
            visit.first_visit_date = first_of_month
        else:
            db.add(Visit(tcc_destination_id=tcc_destination_id, first_visit_date=first_of_month))
    elif visit:
        # No trips visit this destination anymore - clear the visit date
        visit.first_visit_date = None


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
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> TripData:
    """Get a single trip by ID (admin only)."""
    trip = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination),
            joinedload(Trip.participants).joinedload(TripParticipant.user),
            joinedload(Trip.cities),
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
    # Add destinations
    for dest_input in destinations:
        tcc_dest = (
            db.query(TCCDestination)
            .filter(TCCDestination.id == dest_input.tcc_destination_id)
            .first()
        )
        if tcc_dest:
            trip.destinations.append(
                TripDestination(
                    tcc_destination_id=dest_input.tcc_destination_id,
                    is_partial=dest_input.is_partial,
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

    # Add participants
    for user_id in participant_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
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
            joinedload(Trip.cities),
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

    # Update destinations if provided
    if request.destinations is not None:
        # Clear existing and recreate
        trip.destinations.clear()
        for dest_input in request.destinations:
            tcc_dest = (
                db.query(TCCDestination)
                .filter(TCCDestination.id == dest_input.tcc_destination_id)
                .first()
            )
            if tcc_dest:
                trip.destinations.append(
                    TripDestination(
                        tcc_destination_id=dest_input.tcc_destination_id,
                        is_partial=dest_input.is_partial,
                    )
                )

    # Update cities if provided
    if request.cities is not None:
        trip.cities.clear()
        for i, city_input in enumerate(request.cities):
            trip.cities.append(
                TripCity(
                    name=city_input.name,
                    is_partial=city_input.is_partial,
                    order=i,
                )
            )

    # Update participants if provided
    if request.participant_ids is not None:
        trip.participants.clear()
        for user_id in request.participant_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
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
            joinedload(Trip.cities),
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


@router.get("/holidays/{year}/{country_code}", response_model=HolidaysResponse)
def get_holidays(
    year: int,
    country_code: str,
    admin: Annotated[User, Depends(get_admin_user)],
) -> HolidaysResponse:
    """Get public holidays for a year/country from Nager.Date API (admin only).

    Uses in-memory cache with 24h TTL.
    """
    country_code = country_code.upper()
    cache_key = (year, country_code)

    # Check cache
    if cache_key in _holidays_cache:
        cached_holidays, cached_time = _holidays_cache[cache_key]
        if time.time() - cached_time < _HOLIDAYS_CACHE_TTL:
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
            # Country not supported or not found - cache empty result
            _holidays_cache[cache_key] = ([], time.time())
            return HolidaysResponse(holidays=[])

        response.raise_for_status()
        data = response.json()

        # Cache the raw data
        _holidays_cache[cache_key] = (data, time.time())

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
        # Return empty on any error (network, timeout, rate limit, etc.)
        return HolidaysResponse(holidays=[])
