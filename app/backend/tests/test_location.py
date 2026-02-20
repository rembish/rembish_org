"""Tests for location endpoints (check-in, current location, active trip, nearby)."""

from collections.abc import Generator
from datetime import UTC, date, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.session import get_admin_user, get_current_user
from src.database import get_db
from src.main import app
from src.models import City, Trip, TripCity, User, UserLastLocation


def _create_city(
    db: Session,
    name: str = "Prague",
    country: str = "Czech Republic",
    country_code: str = "CZ",
    lat: float = 50.08,
    lng: float = 14.44,
) -> City:
    city = City(
        name=name,
        country=country,
        country_code=country_code,
        lat=lat,
        lng=lng,
        display_name=f"{name}, {country}",
    )
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


# --- Active Trip ---


def test_active_trip_none(admin_client: TestClient) -> None:
    """No active trip returns null."""
    res = admin_client.get("/api/v1/travels/location/active-trip")
    assert res.status_code == 200
    assert res.json()["trip"] is None


def test_active_trip_found(admin_client: TestClient, db_session: Session) -> None:
    """Trip spanning today is returned."""
    today = date.today()
    trip = Trip(
        start_date=today,
        end_date=today,
        description="Today's trip",
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    res = admin_client.get("/api/v1/travels/location/active-trip")
    assert res.status_code == 200
    data = res.json()["trip"]
    assert data is not None
    assert data["id"] == trip.id
    assert data["description"] == "Today's trip"


def test_active_trip_requires_admin(client: TestClient) -> None:
    res = client.get("/api/v1/travels/location/active-trip")
    assert res.status_code == 401


# --- Current Location ---


def test_current_location_none(admin_client: TestClient) -> None:
    """No location recorded returns null."""
    res = admin_client.get("/api/v1/travels/location/current")
    assert res.status_code == 200
    assert res.json() is None


def test_current_location_found(
    admin_client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Returns last recorded admin location."""
    city = _create_city(db_session)
    loc = UserLastLocation(
        user_id=admin_user.id,
        city_id=city.id,
        lat=50.08,
        lng=14.44,
        recorded_at=datetime.now(UTC),
    )
    db_session.add(loc)
    db_session.commit()

    res = admin_client.get("/api/v1/travels/location/current")
    assert res.status_code == 200
    data = res.json()
    assert data["city_name"] == "Prague"
    assert data["country_code"] == "CZ"
    assert data["admin_nickname"] == "admin"


def test_current_location_requires_admin(client: TestClient) -> None:
    res = client.get("/api/v1/travels/location/current")
    assert res.status_code == 401


# --- Check-In ---


def test_check_in(admin_client: TestClient, db_session: Session) -> None:
    """Check-in saves location."""
    city = _create_city(db_session)

    res = admin_client.post(
        "/api/v1/travels/location/check-in",
        json={"city_id": city.id, "lat": 50.08, "lng": 14.44},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["city_name"] == "Prague"

    # Verify DB
    loc = db_session.query(UserLastLocation).first()
    assert loc is not None
    assert loc.city_id == city.id


def test_check_in_updates_existing(
    admin_client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Second check-in updates existing location."""
    city1 = _create_city(db_session, name="Prague")
    city2 = _create_city(db_session, name="Brno", lat=49.2, lng=16.6)

    # First check-in
    admin_client.post(
        "/api/v1/travels/location/check-in",
        json={"city_id": city1.id, "lat": 50.08, "lng": 14.44},
    )

    # Second check-in
    admin_client.post(
        "/api/v1/travels/location/check-in",
        json={"city_id": city2.id, "lat": 49.2, "lng": 16.6},
    )

    locations = db_session.query(UserLastLocation).all()
    assert len(locations) == 1
    assert locations[0].city_id == city2.id


def test_check_in_city_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/location/check-in",
        json={"city_id": 999, "lat": 50.0, "lng": 14.0},
    )
    assert res.status_code == 404


def test_check_in_add_to_trip(admin_client: TestClient, db_session: Session) -> None:
    """Check-in with add_to_trip adds city to active trip."""
    today = date.today()
    trip = Trip(start_date=today, end_date=today)
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    city = _create_city(db_session, name="Vienna", country_code="AT", lat=48.2, lng=16.37)

    res = admin_client.post(
        "/api/v1/travels/location/check-in",
        json={"city_id": city.id, "lat": 48.2, "lng": 16.37, "add_to_trip": True},
    )
    assert res.status_code == 200

    trip_cities = db_session.query(TripCity).filter(TripCity.trip_id == trip.id).all()
    assert len(trip_cities) == 1
    assert trip_cities[0].name == "Vienna"
    assert trip_cities[0].city_id == city.id


def test_check_in_add_to_trip_no_duplicate(
    admin_client: TestClient, db_session: Session
) -> None:
    """Checking in to same city twice doesn't create duplicate trip city."""
    today = date.today()
    trip = Trip(start_date=today, end_date=today)
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    city = _create_city(db_session, name="Vienna", country_code="AT")

    admin_client.post(
        "/api/v1/travels/location/check-in",
        json={"city_id": city.id, "lat": 48.2, "lng": 16.37, "add_to_trip": True},
    )
    admin_client.post(
        "/api/v1/travels/location/check-in",
        json={"city_id": city.id, "lat": 48.2, "lng": 16.37, "add_to_trip": True},
    )

    trip_cities = db_session.query(TripCity).filter(TripCity.trip_id == trip.id).all()
    assert len(trip_cities) == 1


def test_check_in_requires_admin(client: TestClient, db_session: Session) -> None:
    city = _create_city(db_session)
    res = client.post(
        "/api/v1/travels/location/check-in",
        json={"city_id": city.id, "lat": 50.0, "lng": 14.0},
    )
    assert res.status_code == 401


# --- Nearby Cities ---


@patch("src.travels.location._reverse_geocode")
def test_nearby_cities_from_db(
    mock_geocode: object, db_session: Session, admin_user: User
) -> None:
    """Nearby endpoint returns local DB cities within 50km."""
    mock_geocode.return_value = None  # type: ignore[attr-defined]

    _create_city(db_session, name="Prague", lat=50.08, lng=14.44)
    _create_city(db_session, name="Tokyo", lat=35.68, lng=139.69)  # too far

    # Nearby uses get_current_user (not get_admin_user)
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        res = c.get(
            "/api/v1/travels/location/nearby", params={"lat": 50.08, "lng": 14.44}
        )
    app.dependency_overrides.clear()

    assert res.status_code == 200
    data = res.json()
    names = [c["name"] for c in data["cities"]]
    assert "Prague" in names
    assert "Tokyo" not in names


@patch("src.travels.location._reverse_geocode")
def test_nearby_cities_geocoded(
    mock_geocode: object, db_session: Session, admin_user: User
) -> None:
    """Nearby endpoint uses reverse geocoding and caches result."""
    mock_geocode.return_value = {  # type: ignore[attr-defined]
        "name": "Nové Město",
        "country": "Czech Republic",
        "country_code": "CZ",
        "lat": 50.08,
        "lng": 14.44,
    }

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        res = c.get(
            "/api/v1/travels/location/nearby", params={"lat": 50.08, "lng": 14.44}
        )
    app.dependency_overrides.clear()

    assert res.status_code == 200
    data = res.json()
    assert any(c["name"] == "Nové Město" for c in data["cities"])

    # City was cached
    cached = db_session.query(City).filter(City.name == "Nové Město").first()
    assert cached is not None
    assert cached.country_code == "CZ"


def test_nearby_requires_auth(client: TestClient) -> None:
    res = client.get("/api/v1/travels/location/nearby", params={"lat": 50.0, "lng": 14.0})
    assert res.status_code == 401
