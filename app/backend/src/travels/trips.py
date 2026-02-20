import calendar
import json
import logging
import time
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

import httpx
from cachetools import TTLCache
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
from ..models.vault import TripPassport, TripTravelDoc, VaultTravelDoc, VaultVaccination
from .models import (
    CitySearchResponse,
    CitySearchResult,
    CountryHoliday,
    CountryInfoData,
    CountryInfoTCCDestination,
    CurrencyInfo,
    HealthRequirements,
    HealthVaccination,
    HolidaysResponse,
    MalariaInfo,
    PublicHoliday,
    SunriseSunset,
    TCCDestinationOption,
    TCCDestinationOptionsResponse,
    TripCityData,
    TripCityInput,
    TripCountryInfoResponse,
    TripCreateRequest,
    TripData,
    TripDestinationData,
    TripDestinationInput,
    TripParticipantData,
    TripsResponse,
    TripTravelDocInfo,
    TripUpdateRequest,
    UserOption,
    UserOptionsResponse,
    VacationSummary,
    WeatherInfo,
)
from .vacation import ANNUAL_LEAVE_DAYS, count_vacation_days

# Nominatim rate limiting - track last request time
_nominatim_last_request: float = 0.0
_NOMINATIM_COOLDOWN = 1.0  # seconds between requests

# TTL caches for external API responses (auto-evict expired entries, bounded size)
_holidays_cache: TTLCache[tuple[int, str], list[dict]] = TTLCache(maxsize=256, ttl=86400)
_currency_cache: TTLCache[str, dict[str, float] | None] = TTLCache(maxsize=64, ttl=3600)
_weather_cache: TTLCache[tuple[float, float, int], dict[str, float | None | int]] = TTLCache(
    maxsize=256, ttl=86400
)
_sunrise_cache: TTLCache[tuple[float, float, str], SunriseSunset | None] = TTLCache(
    maxsize=256, ttl=86400
)

# Health requirements data: loaded once from static JSON
_health_data: dict[str, dict] = {}
_health_data_path = Path(__file__).parent.parent / "data" / "health_requirements.json"
if _health_data_path.exists():
    with open(_health_data_path) as _f:
        _raw = json.load(_f)
        for _c in _raw.get("countries", []):
            _health_data[_c["country_code"]] = _c

# Czech socket types for adapter comparison
_CZ_SOCKETS = {"C", "E"}

log = logging.getLogger(__name__)

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
            joinedload(Trip.cities).joinedload(TripCity.city),
        )
        .order_by(Trip.start_date.desc())
        .all()
    )

    trips_data = [_trip_to_data(trip) for trip in trips]

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
    country_codes: list[str] | None = None,
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
    elif country_codes:
        # Multiple countries - use countrycodes filter (comma-separated ISO alpha-2)
        params["countrycodes"] = ",".join(c.lower() for c in country_codes)

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
        multi_codes = codes if codes and len(codes) > 1 else None
        nominatim_results = _search_nominatim(
            q, country_name, fallback_code, country_codes=multi_codes
        )
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
                                geocoded_at=datetime.now(UTC),
                                confidence="nominatim",
                            )
                        )
        db.commit()

    return CitySearchResponse(results=results[:10])


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
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> TripData:
    """Get a single trip by ID (admin only)."""
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

    # Batch-validate participants
    if participant_ids:
        valid_users = {u.id for u in db.query(User.id).filter(User.id.in_(participant_ids)).all()}
        for user_id in participant_ids:
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

    # Update participants if changed
    if request.participant_ids is not None:
        existing_ids = sorted(p.user_id for p in trip.participants)
        requested_ids = sorted(request.participant_ids)
        if existing_ids != requested_ids:
            valid_users = (
                {u.id for u in db.query(User.id).filter(User.id.in_(request.participant_ids)).all()}
                if request.participant_ids
                else set()
            )
            trip.participants.clear()
            db.flush()
            for user_id in request.participant_ids:
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
    admin: Annotated[User, Depends(get_admin_user)],
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
    admin: Annotated[User, Depends(get_admin_user)],
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


def _needs_adapter(socket_types: str | None) -> bool | None:
    """Check if country needs a power adapter (compared to Czech C/E)."""
    if not socket_types:
        return None
    country_sockets = {s.strip() for s in socket_types.split(",")}
    # Adapter not needed if country supports C or E (Czech standard)
    return not bool(country_sockets & _CZ_SOCKETS)


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


def _compute_timezone_offset(tz_name: str, ref_date: date) -> float | None:
    """Compute timezone offset from CET in hours."""
    try:
        country_tz = ZoneInfo(tz_name)
        cet_tz = ZoneInfo("Europe/Prague")
        ref_dt = datetime(ref_date.year, ref_date.month, ref_date.day, 12, 0)
        country_offset = ref_dt.replace(tzinfo=country_tz).utcoffset()
        cet_offset = ref_dt.replace(tzinfo=cet_tz).utcoffset()
        if country_offset is None or cet_offset is None:
            return None
        diff_seconds = (country_offset - cet_offset).total_seconds()
        return diff_seconds / 3600
    except Exception:
        return None


def _vaccine_matches(cdc_name: str, user_names: set[str]) -> bool:
    """Check if a CDC vaccine name matches any user vaccination (fuzzy).

    Handles combined vaccines: user's "Hepatitis A+B" covers both
    CDC's "Hepatitis A" and "Hepatitis B".
    """
    cdc_lower = cdc_name.lower()
    # Strip parenthetical suffixes: "Polio (booster)" → "polio"
    base = cdc_lower.split("(")[0].strip()
    for uname in user_names:
        u = uname.lower()
        if u == cdc_lower or u == base or cdc_lower.startswith(u) or u.startswith(base):
            return True
        # Combined vaccines: split on +/& and check each part
        # e.g. "hepatitis a+b" → ["hepatitis a", "hepatitis b"]
        for sep in ("+", "&", " and "):
            if sep in u:
                parts = [p.strip() for p in u.split(sep)]
                # Expand shorthand: ["hepatitis a", "b"] → ["hepatitis a", "hepatitis b"]
                prefix = ""
                expanded = []
                for part in parts:
                    if " " in part:
                        prefix = part.rsplit(" ", 1)[0]
                        expanded.append(part)
                    elif prefix:
                        expanded.append(f"{prefix} {part}")
                    else:
                        expanded.append(part)
                if base in expanded or cdc_lower in expanded:
                    return True
    return False


def _get_health_requirements(
    iso_alpha2: str, user_vaccine_names: set[str] | None = None
) -> HealthRequirements | None:
    """Look up health requirements for a country by ISO alpha-2 code."""
    entry = _health_data.get(iso_alpha2)
    if not entry:
        return None

    names = user_vaccine_names or set()
    vax = entry.get("vaccinations", {})
    required = [
        HealthVaccination(
            vaccine=v["vaccine"],
            priority=v.get("priority", "required"),
            notes=v.get("notes"),
            covered=_vaccine_matches(v["vaccine"], names),
        )
        for v in vax.get("required", [])
    ]
    recommended = [
        HealthVaccination(
            vaccine=v["vaccine"],
            priority=v.get("priority", "recommended"),
            notes=v.get("notes"),
            covered=_vaccine_matches(v["vaccine"], names),
        )
        for v in vax.get("recommended", [])
    ]
    routine = vax.get("routine", [])

    malaria = None
    mal_data = entry.get("malaria")
    if mal_data:
        malaria = MalariaInfo(
            risk=mal_data.get("risk", False),
            areas=mal_data.get("areas"),
            species=mal_data.get("species"),
            prophylaxis=mal_data.get("prophylaxis") or [],
            drug_resistance=mal_data.get("drug_resistance") or [],
        )

    return HealthRequirements(
        vaccinations_required=required,
        vaccinations_recommended=recommended,
        vaccinations_routine=routine,
        malaria=malaria,
        other_risks=entry.get("other_risks", []),
    )


@router.get("/trips/{trip_id}/country-info", response_model=TripCountryInfoResponse)
def get_trip_country_info(
    trip_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> TripCountryInfoResponse:
    """Get aggregated country reference data for a trip's destinations (admin only)."""
    trip = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations)
            .joinedload(TripDestination.tcc_destination)
            .joinedload(TCCDestination.un_country),
        )
        .filter(Trip.id == trip_id)
        .first()
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Get admin's vaccination records for coverage matching
    user_vax_names: set[str] = set()
    vax_records = (
        db.query(VaultVaccination.vaccine_name).filter(VaultVaccination.user_id == admin.id).all()
    )
    for (name,) in vax_records:
        user_vax_names.add(name)

    # Query travel documents: assigned to this trip OR matching by country_code
    trip_travel_docs: dict[str, list[VaultTravelDoc]] = {}
    seen_doc_ids: set[int] = set()

    # Get the trip's assigned passport (to filter visa-passport linkage)
    trip_passport = db.query(TripPassport).filter(TripPassport.trip_id == trip_id).first()
    trip_passport_id = trip_passport.document_id if trip_passport else None

    # 1. Explicitly assigned to this trip
    ttd_rows = (
        db.query(VaultTravelDoc)
        .join(TripTravelDoc, TripTravelDoc.travel_doc_id == VaultTravelDoc.id)
        .filter(TripTravelDoc.trip_id == trip_id)
        .all()
    )
    for vtd in ttd_rows:
        cc = (vtd.country_code or "").upper()
        if cc:
            trip_travel_docs.setdefault(cc, []).append(vtd)
            seen_doc_ids.add(vtd.id)

    # 2. Auto-match: valid docs for trip's destination countries
    today = date.today()

    # Single-entry visas assigned to a completed trip are considered used
    used_single_ids: set[int] = {
        row[0]
        for row in db.query(VaultTravelDoc.id)
        .join(TripTravelDoc, TripTravelDoc.travel_doc_id == VaultTravelDoc.id)
        .join(Trip, Trip.id == TripTravelDoc.trip_id)
        .filter(
            VaultTravelDoc.entry_type == "single",
            Trip.end_date.isnot(None),
            Trip.end_date < today,
        )
        .all()
    }

    country_docs = (
        db.query(VaultTravelDoc)
        .filter(
            VaultTravelDoc.country_code.isnot(None),
            (VaultTravelDoc.valid_until.is_(None)) | (VaultTravelDoc.valid_until >= today),
        )
        .all()
    )
    for vtd in country_docs:
        if vtd.id in seen_doc_ids:
            continue
        if vtd.id in used_single_ids:
            continue
        # Skip visas linked to a different passport than the trip's passport
        if vtd.document_id and trip_passport_id and vtd.document_id != trip_passport_id:
            continue
        cc = (vtd.country_code or "").upper()
        if cc:
            trip_travel_docs.setdefault(cc, []).append(vtd)

    # Group TCC destinations by UN country
    # Key: un_country_id (or negative tcc_id for orphans)
    grouped: dict[int, tuple[UNCountry | None, list[tuple[str, bool]]]] = {}
    for td in trip.destinations:
        tcc = td.tcc_destination
        un = tcc.un_country
        key = un.id if un else -tcc.id
        if key not in grouped:
            grouped[key] = (un, [])
        grouped[key][1].append((tcc.name, td.is_partial))

    trip_start = trip.start_date
    trip_end = trip.end_date or trip.start_date
    # Use mid-trip date for weather month
    mid_trip = trip_start + (trip_end - trip_start) / 2
    trip_month = mid_trip.month

    countries: list[CountryInfoData] = []
    for _key, (un_country, tcc_dests) in sorted(
        grouped.items(),
        key=lambda x: x[1][0].name if x[1][0] else x[1][1][0][0],
    ):
        if un_country:
            country_name = un_country.name
            iso = un_country.iso_alpha2

            # Currency
            currency = None
            if un_country.currency_code:
                rates = _fetch_currency_rates(un_country.currency_code)
                currency = CurrencyInfo(
                    code=un_country.currency_code,
                    name=_get_currency_name(un_country.currency_code),
                    rates=rates,
                )

            # Weather
            weather = None
            if un_country.capital_lat is not None and un_country.capital_lng is not None:
                w = _fetch_weather(un_country.capital_lat, un_country.capital_lng, trip_month)
                rainy_days_val = w.get("rainy_days")
                weather = WeatherInfo(
                    avg_temp_c=w.get("avg_temp_c"),
                    min_temp_c=w.get("min_temp_c"),
                    max_temp_c=w.get("max_temp_c"),
                    avg_precipitation_mm=w.get("avg_precipitation_mm"),
                    rainy_days=int(rainy_days_val) if rainy_days_val is not None else None,
                    month=calendar.month_name[trip_month],
                )

            # Timezone
            tz_offset = None
            if un_country.timezone:
                tz_offset = _compute_timezone_offset(un_country.timezone, trip_start)

            # Holidays
            holidays = _fetch_holidays_for_country(iso, trip_start, trip_end)

            # Sunrise/sunset for mid-trip date
            sunrise_sunset = None
            if un_country.capital_lat is not None and un_country.capital_lng is not None:
                sunrise_sunset = _fetch_sunrise_sunset(
                    un_country.capital_lat,
                    un_country.capital_lng,
                    mid_trip,
                    tz_offset,
                )

            countries.append(
                CountryInfoData(
                    country_name=country_name,
                    iso_alpha2=iso,
                    tcc_destinations=[
                        CountryInfoTCCDestination(name=n, is_partial=p) for n, p in tcc_dests
                    ],
                    socket_types=un_country.socket_types,
                    voltage=un_country.voltage,
                    phone_code=un_country.phone_code,
                    driving_side=un_country.driving_side,
                    emergency_number=un_country.emergency_number,
                    tap_water=un_country.tap_water,
                    currency=currency,
                    weather=weather,
                    timezone_offset_hours=tz_offset,
                    holidays=holidays,
                    languages=un_country.languages,
                    tipping=un_country.tipping,
                    speed_limits=un_country.speed_limits,
                    visa_free_days=un_country.visa_free_days,
                    eu_roaming=un_country.eu_roaming,
                    adapter_needed=_needs_adapter(un_country.socket_types),
                    sunrise_sunset=sunrise_sunset,
                    health=_get_health_requirements(iso, user_vax_names),
                    travel_docs=[
                        TripTravelDocInfo(
                            id=vtd.id,
                            doc_type=vtd.doc_type,
                            label=vtd.label,
                            valid_until=vtd.valid_until.isoformat() if vtd.valid_until else None,
                            entry_type=vtd.entry_type,
                            passport_label=vtd.passport.label if vtd.passport else None,
                            expires_before_trip=bool(
                                vtd.valid_until and vtd.valid_until < trip_end
                            ),
                            has_files=len(vtd.files) > 0 if vtd.files else False,
                        )
                        for vtd in trip_travel_docs.get(iso, [])
                    ],
                )
            )
        else:
            # Orphan TCC destination (e.g., Kosovo) — minimal card
            name = tcc_dests[0][0] if tcc_dests else "Unknown"
            countries.append(
                CountryInfoData(
                    country_name=name,
                    iso_alpha2="",
                    tcc_destinations=[
                        CountryInfoTCCDestination(name=n, is_partial=p) for n, p in tcc_dests
                    ],
                    socket_types=None,
                    voltage=None,
                    phone_code=None,
                    driving_side=None,
                    emergency_number=None,
                    tap_water=None,
                    currency=None,
                    weather=None,
                    timezone_offset_hours=None,
                    holidays=[],
                    languages=None,
                    tipping=None,
                    speed_limits=None,
                    visa_free_days=None,
                    eu_roaming=None,
                    adapter_needed=None,
                    sunrise_sunset=None,
                )
            )

    return TripCountryInfoResponse(countries=countries)
