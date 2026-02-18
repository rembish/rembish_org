"""Tests for flight tracking API."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Airport, Flight, Trip, UNCountry


def _create_trip(db: Session) -> Trip:
    trip = Trip(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 20),
        trip_type="regular",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def _create_airport(
    db: Session,
    iata: str,
    name: str | None = None,
    country_code: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Airport:
    airport = Airport(
        iata_code=iata,
        name=name,
        country_code=country_code,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(airport)
    db.commit()
    db.refresh(airport)
    return airport


def test_list_flights_empty(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/flights")
    assert res.status_code == 200
    data = res.json()
    assert data["flights"] == []


def test_create_flight(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-10",
            "flight_number": "TK1770",
            "airline_name": "Turkish Airlines",
            "departure_iata": "PRG",
            "arrival_iata": "IST",
            "departure_time": "06:30",
            "arrival_time": "10:15",
            "terminal": "2",
            "aircraft_type": "Airbus A321",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["flight_number"] == "TK1770"
    assert data["airline_name"] == "Turkish Airlines"
    assert data["departure_airport"]["iata_code"] == "PRG"
    assert data["arrival_airport"]["iata_code"] == "IST"
    assert data["departure_time"] == "06:30"
    assert data["arrival_time"] == "10:15"
    assert data["aircraft_type"] == "Airbus A321"
    assert data["id"] > 0

    # Airports were created
    prg = db_session.query(Airport).filter(Airport.iata_code == "PRG").first()
    assert prg is not None
    ist = db_session.query(Airport).filter(Airport.iata_code == "IST").first()
    assert ist is not None


def test_create_flight_manual(admin_client: TestClient, db_session: Session) -> None:
    """Manual entry with just IATA codes, no API."""
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-15",
            "flight_number": "XX999",
            "departure_iata": "JFK",
            "arrival_iata": "LAX",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["flight_number"] == "XX999"
    assert data["departure_airport"]["iata_code"] == "JFK"
    assert data["arrival_airport"]["iata_code"] == "LAX"
    assert data["airline_name"] is None
    assert data["departure_time"] is None


def test_create_flight_upserts_airport(admin_client: TestClient, db_session: Session) -> None:
    """Creating two flights with the same airport reuses the airport record."""
    trip = _create_trip(db_session)

    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-10",
            "flight_number": "AB100",
            "departure_iata": "PRG",
            "arrival_iata": "FRA",
        },
    )
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-12",
            "flight_number": "AB200",
            "departure_iata": "FRA",
            "arrival_iata": "PRG",
        },
    )

    # PRG and FRA should each exist once
    prg_count = db_session.query(Airport).filter(Airport.iata_code == "PRG").count()
    fra_count = db_session.query(Airport).filter(Airport.iata_code == "FRA").count()
    assert prg_count == 1
    assert fra_count == 1


def test_delete_flight(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    dep = _create_airport(db_session, "PRG")
    arr = _create_airport(db_session, "IST")

    flight = Flight(
        trip_id=trip.id,
        flight_date=date(2026, 3, 10),
        flight_number="TK1770",
        departure_airport_id=dep.id,
        arrival_airport_id=arr.id,
    )
    db_session.add(flight)
    db_session.commit()
    db_session.refresh(flight)

    res = admin_client.delete(f"/api/v1/travels/flights/{flight.id}")
    assert res.status_code == 204

    # Verify deleted
    assert db_session.query(Flight).filter(Flight.id == flight.id).first() is None


def test_delete_flight_not_found(admin_client: TestClient) -> None:
    res = admin_client.delete("/api/v1/travels/flights/999")
    assert res.status_code == 404


def test_flights_require_admin(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = client.get(f"/api/v1/travels/trips/{trip.id}/flights")
    assert res.status_code == 401


def test_lookup_no_api_key(admin_client: TestClient) -> None:
    """Without AERODATABOX_API_KEY, lookup returns 501."""
    res = admin_client.get(
        "/api/v1/travels/flights/lookup",
        params={"flight_number": "TK1770", "date": "2026-03-10"},
    )
    assert res.status_code == 501


def test_flights_ordered_by_date(admin_client: TestClient, db_session: Session) -> None:
    """Flights are returned ordered by date then departure time."""
    trip = _create_trip(db_session)

    # Create flights in reverse order
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-15",
            "flight_number": "AB200",
            "departure_iata": "IST",
            "arrival_iata": "PRG",
            "departure_time": "14:00",
        },
    )
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-10",
            "flight_number": "AB100",
            "departure_iata": "PRG",
            "arrival_iata": "IST",
            "departure_time": "06:30",
        },
    )

    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/flights")
    flights = res.json()["flights"]
    assert len(flights) == 2
    assert flights[0]["flight_number"] == "AB100"
    assert flights[1]["flight_number"] == "AB200"


def test_create_flight_with_arrival_date(admin_client: TestClient, db_session: Session) -> None:
    """Overnight flights store arrival_date."""
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-10",
            "flight_number": "SN256",
            "departure_iata": "ABJ",
            "arrival_iata": "BRU",
            "departure_time": "22:30",
            "arrival_time": "06:15",
            "arrival_date": "2026-03-11",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["flight_date"] == "2026-03-10"
    assert data["arrival_date"] == "2026-03-11"


def test_flights_count_auto_sync(admin_client: TestClient, db_session: Session) -> None:
    """Adding flights auto-updates trip.flights_count."""
    trip = _create_trip(db_session)

    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-10",
            "flight_number": "AB100",
            "departure_iata": "PRG",
            "arrival_iata": "FRA",
        },
    )
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights",
        json={
            "flight_date": "2026-03-12",
            "flight_number": "AB200",
            "departure_iata": "FRA",
            "arrival_iata": "PRG",
        },
    )

    db_session.refresh(trip)
    assert trip.flights_count == 2


def test_flights_count_self_heal(admin_client: TestClient, db_session: Session) -> None:
    """Viewing transport tab corrects stale flights_count."""
    trip = _create_trip(db_session)
    dep = _create_airport(db_session, "PRG")
    arr = _create_airport(db_session, "IST")

    # Create flights directly (bypassing auto-sync)
    for fn in ("AB1", "AB2", "AB3"):
        db_session.add(
            Flight(
                trip_id=trip.id,
                flight_date=date(2026, 3, 10),
                flight_number=fn,
                departure_airport_id=dep.id,
                arrival_airport_id=arr.id,
            )
        )
    db_session.commit()

    # flights_count is stale (None)
    assert trip.flights_count is None

    # GET triggers self-heal
    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/flights")
    assert res.status_code == 200
    assert len(res.json()["flights"]) == 3

    db_session.refresh(trip)
    assert trip.flights_count == 3


def test_flight_dates_endpoint(admin_client: TestClient, db_session: Session) -> None:
    """GET /flights/dates returns flight dates with arrival country codes."""
    trip = _create_trip(db_session)
    dep = _create_airport(db_session, "PRG", country_code="CZ")
    arr = _create_airport(db_session, "IST", country_code="TR")

    for d in (date(2026, 1, 10), date(2026, 1, 10), date(2026, 1, 15)):
        db_session.add(
            Flight(
                trip_id=trip.id,
                flight_date=d,
                flight_number="AB1",
                departure_airport_id=dep.id,
                arrival_airport_id=arr.id,
            )
        )
    db_session.commit()

    res = admin_client.get("/api/v1/travels/flights/dates", params={"year": 2026})
    assert res.status_code == 200
    dates = res.json()["dates"]
    assert dates == {"2026-01-10": ["TR"], "2026-01-15": ["TR"]}

    # Wrong year returns empty
    res2 = admin_client.get("/api/v1/travels/flights/dates", params={"year": 2025})
    assert res2.json()["dates"] == {}


def test_map_flights_endpoint(client: TestClient, db_session: Session) -> None:
    """GET /map-flights is public and returns airports, routes, country_regions."""
    trip = _create_trip(db_session)
    prg = _create_airport(db_session, "PRG", "Prague", "CZ", 50.1, 14.26)
    ist = _create_airport(db_session, "IST", "Istanbul", "TR", 40.98, 28.82)

    # Create UN countries for region mapping
    cz = UNCountry(
        name="Czechia",
        iso_alpha2="CZ",
        iso_alpha3="CZE",
        iso_numeric="203",
        continent="Europe",
        map_region_codes="203",
    )
    tr = UNCountry(
        name="Turkey",
        iso_alpha2="TR",
        iso_alpha3="TUR",
        iso_numeric="792",
        continent="Asia",
        map_region_codes="792",
    )
    db_session.add_all([cz, tr])
    db_session.commit()

    # Create two flights PRG→IST (past date)
    for fn in ("TK1", "TK2"):
        db_session.add(
            Flight(
                trip_id=trip.id,
                flight_date=date(2026, 1, 10),
                flight_number=fn,
                departure_airport_id=prg.id,
                arrival_airport_id=ist.id,
            )
        )
    db_session.commit()

    res = client.get("/api/v1/travels/map-flights")
    assert res.status_code == 200
    data = res.json()

    # 2 airports with coordinates
    assert len(data["airports"]) == 2
    iatas = {a["iata_code"] for a in data["airports"]}
    assert iatas == {"PRG", "IST"}

    # 1 route (normalized direction) with count=2
    assert len(data["routes"]) == 1
    route = data["routes"][0]
    assert route["count"] == 2

    # Country regions: dict with airport counts
    assert data["country_regions"]["203"] == 1  # CZ: 1 airport (PRG)
    assert data["country_regions"]["792"] == 1  # TR: 1 airport (IST)


def test_map_flights_no_coords(client: TestClient, db_session: Session) -> None:
    """Airports without coordinates are excluded from map data."""
    trip = _create_trip(db_session)
    prg = _create_airport(db_session, "PRG")  # no lat/lng
    ist = _create_airport(db_session, "IST")  # no lat/lng

    db_session.add(
        Flight(
            trip_id=trip.id,
            flight_date=date(2026, 1, 10),
            flight_number="TK1",
            departure_airport_id=prg.id,
            arrival_airport_id=ist.id,
        )
    )
    db_session.commit()

    res = client.get("/api/v1/travels/map-flights")
    assert res.status_code == 200
    data = res.json()
    assert data["airports"] == []
    assert data["routes"] == []
