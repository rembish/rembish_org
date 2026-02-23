"""Tests for drones and drone flights API."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Drone, DroneFlight, Trip


def _create_drone(db: Session, name: str = "test.drone", model: str = "Test Model") -> Drone:
    drone = Drone(name=name, model=model)
    db.add(drone)
    db.commit()
    db.refresh(drone)
    return drone


def _create_trip(db: Session) -> Trip:
    trip = Trip(start_date=date(2025, 6, 1), end_date=date(2025, 6, 15), trip_type="regular")
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def _create_flight(
    db: Session,
    drone: Drone | None = None,
    trip: Trip | None = None,
    flight_date: date = date(2025, 6, 5),
    is_hidden: bool = False,
    latitude: float | None = 40.0,
    longitude: float | None = 20.0,
    country: str | None = "GR",
) -> DroneFlight:
    f = DroneFlight(
        drone_id=drone.id if drone else None,
        trip_id=trip.id if trip else None,
        flight_date=flight_date,
        latitude=latitude,
        longitude=longitude,
        duration_sec=300.0,
        distance_km=1.5,
        photos=10,
        video_sec=120,
        country=country,
        city="Athens",
        is_hidden=is_hidden,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


# ---------------------------------------------------------------------------
# Drones CRUD
# ---------------------------------------------------------------------------


def test_list_drones_empty(admin_client: TestClient, db_session: Session) -> None:
    res = admin_client.get("/api/v1/travels/drones")
    assert res.status_code == 200
    assert res.json()["drones"] == []


def test_create_drone(admin_client: TestClient, db_session: Session) -> None:
    res = admin_client.post(
        "/api/v1/travels/drones",
        json={"name": "air2.rembish.org", "model": "Mavic Air 2"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "air2.rembish.org"
    assert data["model"] == "Mavic Air 2"
    assert data["flights_count"] == 0
    assert data["id"] > 0


def test_update_drone(admin_client: TestClient, db_session: Session) -> None:
    drone = _create_drone(db_session)
    res = admin_client.put(
        f"/api/v1/travels/drones/{drone.id}",
        json={"name": "updated.drone", "model": "New Model", "serial_number": "SN123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "updated.drone"
    assert data["serial_number"] == "SN123"


def test_delete_drone(admin_client: TestClient, db_session: Session) -> None:
    drone = _create_drone(db_session)
    _create_flight(db_session, drone=drone)
    res = admin_client.delete(f"/api/v1/travels/drones/{drone.id}")
    assert res.status_code == 204
    # Flight should still exist but with drone_id = NULL
    f = db_session.query(DroneFlight).first()
    assert f is not None
    assert f.drone_id is None


# ---------------------------------------------------------------------------
# Drone Flights CRUD
# ---------------------------------------------------------------------------


def test_list_drone_flights_empty(admin_client: TestClient, db_session: Session) -> None:
    res = admin_client.get("/api/v1/travels/drone-flights")
    assert res.status_code == 200
    data = res.json()
    assert data["flights"] == []
    assert data["total"] == 0


def test_create_drone_flight(admin_client: TestClient, db_session: Session) -> None:
    drone = _create_drone(db_session)
    res = admin_client.post(
        "/api/v1/travels/drone-flights",
        json={
            "drone_id": drone.id,
            "flight_date": "2025-06-05",
            "latitude": 40.0,
            "longitude": 20.0,
            "duration_sec": 300.0,
            "distance_km": 1.5,
            "country": "GR",
            "city": "Athens",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["flight_date"] == "2025-06-05"
    assert data["drone_name"] == "test.drone"
    assert data["country"] == "GR"


def test_create_drone_flight_with_trip(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = admin_client.post(
        "/api/v1/travels/drone-flights",
        json={"flight_date": "2025-06-05", "trip_id": trip.id},
    )
    assert res.status_code == 200
    assert res.json()["trip_id"] == trip.id


def test_update_drone_flight(admin_client: TestClient, db_session: Session) -> None:
    drone = _create_drone(db_session)
    f = _create_flight(db_session, drone=drone)
    res = admin_client.put(
        f"/api/v1/travels/drone-flights/{f.id}",
        json={
            "flight_date": "2025-06-06",
            "drone_id": drone.id,
            "city": "Thessaloniki",
            "country": "GR",
        },
    )
    assert res.status_code == 200
    assert res.json()["city"] == "Thessaloniki"


def test_delete_drone_flight(admin_client: TestClient, db_session: Session) -> None:
    f = _create_flight(db_session)
    res = admin_client.delete(f"/api/v1/travels/drone-flights/{f.id}")
    assert res.status_code == 204
    assert db_session.query(DroneFlight).filter(DroneFlight.id == f.id).first() is None


# ---------------------------------------------------------------------------
# Hide/unhide toggle
# ---------------------------------------------------------------------------


def test_toggle_hide(admin_client: TestClient, db_session: Session) -> None:
    f = _create_flight(db_session)
    assert not f.is_hidden

    res = admin_client.put(f"/api/v1/travels/drone-flights/{f.id}/hide")
    assert res.status_code == 200
    assert res.json()["is_hidden"] is True

    res = admin_client.put(f"/api/v1/travels/drone-flights/{f.id}/hide")
    assert res.status_code == 200
    assert res.json()["is_hidden"] is False


# ---------------------------------------------------------------------------
# Trip assignment
# ---------------------------------------------------------------------------


def test_assign_trip(admin_client: TestClient, db_session: Session) -> None:
    f = _create_flight(db_session)
    trip = _create_trip(db_session)

    res = admin_client.put(
        f"/api/v1/travels/drone-flights/{f.id}/trip?trip_id={trip.id}",
    )
    assert res.status_code == 200
    assert res.json()["trip_id"] == trip.id

    # Unassign
    res = admin_client.put(f"/api/v1/travels/drone-flights/{f.id}/trip")
    assert res.status_code == 200
    assert res.json()["trip_id"] is None


def test_trip_delete_keeps_flight(admin_client: TestClient, db_session: Session) -> None:
    """Deleting a trip does not cascade-delete drone flights (passive_deletes)."""
    trip = _create_trip(db_session)
    f = _create_flight(db_session, trip=trip)
    flight_id = f.id
    assert f.trip_id == trip.id

    # SQLite doesn't enforce ON DELETE SET NULL, so we can't test the NULL
    # behavior here. Instead verify the flight survives trip deletion
    # (passive_deletes=True means SQLAlchemy won't cascade).
    db_session.delete(trip)
    db_session.commit()

    remaining = db_session.query(DroneFlight).filter(DroneFlight.id == flight_id).first()
    assert remaining is not None


# ---------------------------------------------------------------------------
# Stats (public)
# ---------------------------------------------------------------------------


def test_stats_public_no_auth(client: TestClient, db_session: Session) -> None:
    """Stats endpoint works without authentication."""
    res = client.get("/api/v1/travels/drone-stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_flights"] == 0


def test_stats_excludes_hidden(admin_client: TestClient, db_session: Session) -> None:
    drone = _create_drone(db_session)
    _create_flight(db_session, drone=drone, is_hidden=False, country="GR")
    _create_flight(
        db_session,
        drone=drone,
        is_hidden=True,
        flight_date=date(2025, 6, 6),
        country="AL",
    )

    res = admin_client.get("/api/v1/travels/drone-stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_flights"] == 1
    assert data["total_countries"] == 1


def test_stats_by_year_and_drone(admin_client: TestClient, db_session: Session) -> None:
    drone = _create_drone(db_session, name="d1", model="Model A")
    _create_flight(db_session, drone=drone, flight_date=date(2024, 3, 1), country="GR")
    _create_flight(db_session, drone=drone, flight_date=date(2025, 6, 5), country="AL")

    res = admin_client.get("/api/v1/travels/drone-stats")
    data = res.json()
    assert data["total_flights"] == 2
    assert len(data["by_year"]) == 2
    assert data["by_year"][0]["year"] == 2024
    assert data["by_year"][1]["year"] == 2025
    assert len(data["by_drone"]) == 1
    assert data["by_drone"][0]["drone_name"] == "d1"


# ---------------------------------------------------------------------------
# Auth checks
# ---------------------------------------------------------------------------


def test_drones_require_auth(client: TestClient, db_session: Session) -> None:
    """Unauthenticated requests to drones CRUD fail."""
    res = client.get("/api/v1/travels/drones")
    assert res.status_code == 401


def test_drone_flights_require_auth(client: TestClient, db_session: Session) -> None:
    """Unauthenticated requests to drone flights list fail."""
    res = client.get("/api/v1/travels/drone-flights")
    assert res.status_code == 401
