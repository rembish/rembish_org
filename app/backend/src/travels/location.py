import time
from datetime import date, datetime
from math import atan2, cos, radians, sin, sqrt
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user, get_current_user
from ..database import get_db
from ..models import (
    City,
    TCCDestination,
    Trip,
    TripCity,
    TripDestination,
    UNCountry,
    User,
    UserLastLocation,
    Visit,
)

router = APIRouter()

# Nominatim rate limiting
_nominatim_last_request: float = 0.0
_NOMINATIM_COOLDOWN = 1.0  # seconds between requests


# Pydantic models for location endpoints
class NearbyCityData(BaseModel):
    id: int
    name: str
    country: str | None
    country_code: str | None
    lat: float
    lng: float
    distance_km: float


class NearbyCitiesResponse(BaseModel):
    cities: list[NearbyCityData]


class CheckInRequest(BaseModel):
    city_id: int
    lat: float
    lng: float
    add_to_trip: bool = False
    is_partial: bool = False


class CheckInResponse(BaseModel):
    success: bool
    city_name: str
    recorded_at: str


class CurrentLocationResponse(BaseModel):
    city_id: int
    city_name: str
    country: str | None
    country_code: str | None
    lat: float
    lng: float
    recorded_at: str
    # Admin info for display
    admin_nickname: str | None
    admin_picture: str | None


class ActiveTripData(BaseModel):
    id: int
    start_date: str
    end_date: str | None
    description: str | None


class ActiveTripResponse(BaseModel):
    trip: ActiveTripData | None


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def _reverse_geocode(lat: float, lng: float) -> dict | None:
    """Reverse geocode coordinates to get city info. Returns None on error."""
    global _nominatim_last_request

    # Enforce cooldown
    elapsed = time.time() - _nominatim_last_request
    if elapsed < _NOMINATIM_COOLDOWN:
        time.sleep(_NOMINATIM_COOLDOWN - elapsed)

    try:
        _nominatim_last_request = time.time()
        response = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lng,
                "format": "json",
                "addressdetails": 1,
                "zoom": 14,  # Suburb/village level (10 misses small settlements)
            },
            headers={
                "User-Agent": "rembish.org travel tracker (hobby project)",
                "Accept-Language": "en",
            },
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return None

        address = data.get("address", {})

        # Get city name from address (ordered from most to least specific)
        city_name = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("hamlet")
            or address.get("suburb")
            or address.get("county")
            or address.get("state_district")
        )

        if not city_name:
            return None

        # Strip administrative prefixes (Commune de, District de, etc.)
        for prefix in (
            "Commune de ",
            "Commune d'",
            "Commune du ",
            "District de ",
            "District d'",
            "District du ",
            "Département de ",
            "Département d'",
            "Département du ",
            "Municipality of ",
            "City of ",
            "Municipio de ",
            "Municipio del ",
            "Prefeitura de ",
            "Concelho de ",
        ):
            if city_name.startswith(prefix):
                city_name = city_name[len(prefix) :]
                break

        return {
            "name": city_name,
            "country": address.get("country"),
            "country_code": address.get("country_code", "").upper() or None,
            "lat": float(data.get("lat", lat)),
            "lng": float(data.get("lon", lng)),
        }
    except Exception:
        return None


@router.get("/location/nearby", response_model=NearbyCitiesResponse)
def get_nearby_cities(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
) -> NearbyCitiesResponse:
    """Find cities within 50km radius of given coordinates.

    Uses local database + Nominatim reverse geocoding.
    """
    nearby: list[NearbyCityData] = []
    seen_names: set[str] = set()

    # First, reverse geocode to find the city at the user's exact location
    geocoded = _reverse_geocode(lat, lng)
    if geocoded:
        city_name = geocoded["name"]
        name_lower = city_name.lower()

        # Check if city exists in local DB
        existing = (
            db.query(City)
            .filter(
                City.name == city_name,
                City.country_code == geocoded["country_code"],
            )
            .first()
        )

        if existing:
            distance = haversine_km(lat, lng, existing.lat or lat, existing.lng or lng)
            nearby.append(
                NearbyCityData(
                    id=existing.id,
                    name=existing.name,
                    country=existing.country,
                    country_code=existing.country_code,
                    lat=existing.lat or geocoded["lat"],
                    lng=existing.lng or geocoded["lng"],
                    distance_km=round(distance, 2),
                )
            )
            seen_names.add(name_lower)
        else:
            # Cache new city to database
            new_city = City(
                name=city_name,
                country=geocoded["country"],
                country_code=geocoded["country_code"],
                display_name=f"{city_name}, {geocoded['country']}"
                if geocoded["country"]
                else city_name,
                lat=geocoded["lat"],
                lng=geocoded["lng"],
                geocoded_at=datetime.utcnow(),
                confidence="nominatim",
            )
            db.add(new_city)
            db.flush()  # Get the ID

            # new_city.lat/lng are guaranteed non-None since we just set them above
            city_lat = geocoded["lat"]
            city_lng = geocoded["lng"]
            distance = haversine_km(lat, lng, city_lat, city_lng)
            nearby.append(
                NearbyCityData(
                    id=new_city.id,
                    name=new_city.name,
                    country=new_city.country,
                    country_code=new_city.country_code,
                    lat=city_lat,
                    lng=city_lng,
                    distance_km=round(distance, 2),
                )
            )
            seen_names.add(name_lower)
            db.commit()

    # Also search local database for other nearby cities within 50km
    local_cities = db.query(City).filter(City.lat.isnot(None), City.lng.isnot(None)).all()

    for city in local_cities:
        if city.lat is None or city.lng is None:
            continue
        name_lower = city.name.lower()
        if name_lower in seen_names:
            continue

        distance = haversine_km(lat, lng, city.lat, city.lng)
        if distance <= 50:
            nearby.append(
                NearbyCityData(
                    id=city.id,
                    name=city.name,
                    country=city.country,
                    country_code=city.country_code,
                    lat=city.lat,
                    lng=city.lng,
                    distance_km=round(distance, 2),
                )
            )
            seen_names.add(name_lower)

    # Sort by distance and limit to 4
    nearby.sort(key=lambda c: c.distance_km)
    return NearbyCitiesResponse(cities=nearby[:4])


@router.post("/location/check-in", response_model=CheckInResponse)
def check_in_location(
    request: CheckInRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> CheckInResponse:
    """Save current location. Admin only."""
    # Verify city exists
    city = db.query(City).filter(City.id == request.city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    now = datetime.utcnow()

    # Upsert user location
    location = db.query(UserLastLocation).filter(UserLastLocation.user_id == admin.id).first()
    if location:
        location.city_id = request.city_id
        location.lat = request.lat
        location.lng = request.lng
        location.recorded_at = now
    else:
        location = UserLastLocation(
            user_id=admin.id,
            city_id=request.city_id,
            lat=request.lat,
            lng=request.lng,
            recorded_at=now,
        )
        db.add(location)

    # If add_to_trip is requested, find active trip
    if request.add_to_trip:
        today = date.today()

        active_trip = (
            db.query(Trip)
            .filter(
                # Multi-day trip: start_date <= today <= end_date
                # Single-day trip (no end_date): start_date == today
                ((Trip.start_date <= today) & (Trip.end_date >= today))
                | ((Trip.end_date.is_(None)) & (Trip.start_date == today)),
            )
            .first()
        )
        if active_trip:
            # Check if city already in trip
            existing_city = (
                db.query(TripCity)
                .filter(TripCity.trip_id == active_trip.id, TripCity.name == city.name)
                .first()
            )
            if not existing_city:
                # Get max order
                max_order = (
                    db.query(TripCity)
                    .filter(TripCity.trip_id == active_trip.id)
                    .order_by(TripCity.order.desc())
                    .first()
                )
                new_order = (max_order.order + 1) if max_order else 0
                db.add(
                    TripCity(
                        trip_id=active_trip.id,
                        name=city.name,
                        is_partial=request.is_partial,
                        order=new_order,
                        city_id=city.id,
                    )
                )

            # Update first_visit_date for destinations matching city's country
            # Use today's date - the actual check-in date is most precise
            if city.country_code:
                city_code = city.country_code.lower()
                visit_date = date.today()
                # Find matching destinations (check TCC iso_alpha2 first, then UN country)
                matching_destinations = (
                    db.query(TripDestination)
                    .join(TCCDestination)
                    .outerjoin(UNCountry, UNCountry.id == TCCDestination.un_country_id)
                    .filter(TripDestination.trip_id == active_trip.id)
                    .filter(
                        (func.lower(TCCDestination.iso_alpha2) == city_code)
                        | (
                            TCCDestination.iso_alpha2.is_(None)
                            & (func.lower(UNCountry.iso_alpha2) == city_code)
                        )
                    )
                    .all()
                )
                for td in matching_destinations:
                    visit = (
                        db.query(Visit)
                        .filter(Visit.tcc_destination_id == td.tcc_destination_id)
                        .first()
                    )
                    if visit:
                        # Update if no date set or if trip start is earlier
                        if visit.first_visit_date is None or visit.first_visit_date > visit_date:
                            visit.first_visit_date = visit_date
                    else:
                        # Create new visit record with trip's start date
                        db.add(
                            Visit(
                                tcc_destination_id=td.tcc_destination_id,
                                first_visit_date=visit_date,
                            )
                        )

    db.commit()

    return CheckInResponse(
        success=True,
        city_name=city.name,
        recorded_at=now.isoformat(),
    )


@router.get("/location/current")
def get_current_location(
    user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> CurrentLocationResponse | None:
    """Get site owner's last recorded location. Requires login."""
    # Find the admin user's location (site owner) - shown to all logged-in users
    location = (
        db.query(UserLastLocation)
        .join(User)
        .options(joinedload(UserLastLocation.city), joinedload(UserLastLocation.user))
        .filter(User.is_admin == True)  # noqa: E712
        .order_by(UserLastLocation.recorded_at.desc())
        .first()
    )

    if not location:
        return None

    return CurrentLocationResponse(
        city_id=location.city_id,
        city_name=location.city.name,
        country=location.city.country,
        country_code=location.city.country_code,
        lat=location.lat,
        lng=location.lng,
        recorded_at=location.recorded_at.isoformat(),
        admin_nickname=location.user.nickname or location.user.name,
        admin_picture=location.user.picture,
    )


@router.get("/location/active-trip", response_model=ActiveTripResponse)
def get_active_trip(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> ActiveTripResponse:
    """Get trip that spans today. Admin only (used by location check-in modal).

    Trips without end_date are single-day trips (only active on start_date).
    """
    today = date.today()

    trip = (
        db.query(Trip)
        .filter(
            ((Trip.start_date <= today) & (Trip.end_date >= today))
            | ((Trip.end_date.is_(None)) & (Trip.start_date == today))
        )
        .first()
    )

    if not trip:
        return ActiveTripResponse(trip=None)

    return ActiveTripResponse(
        trip=ActiveTripData(
            id=trip.id,
            start_date=trip.start_date.isoformat(),
            end_date=trip.end_date.isoformat() if trip.end_date else None,
            description=trip.description,
        )
    )
