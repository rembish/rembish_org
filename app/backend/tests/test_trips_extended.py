"""Extended trip tests: city search, full CRUD with relations, holidays, helpers."""

from datetime import date
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import City, TCCDestination, Trip, TripDestination, UNCountry, User


def _create_country(
    db: Session,
    *,
    name: str = "Testland",
    iso2: str = "TL",
    iso3: str = "TLD",
    iso_num: str = "999",
    continent: str = "Europe",
    currency_code: str | None = "EUR",
    capital_lat: float | None = 50.0,
    capital_lng: float | None = 14.0,
    timezone: str | None = "Europe/Prague",
    socket_types: str | None = "C,F",
) -> UNCountry:
    country = UNCountry(
        name=name,
        iso_alpha2=iso2,
        iso_alpha3=iso3,
        iso_numeric=iso_num,
        continent=continent,
        map_region_codes=iso2,
        currency_code=currency_code,
        capital_lat=capital_lat,
        capital_lng=capital_lng,
        timezone=timezone,
        socket_types=socket_types,
    )
    db.add(country)
    db.flush()
    return country


def _create_tcc(
    db: Session,
    *,
    name: str = "Test City",
    region: str = "EUROPE",
    tcc_index: int = 1,
    un_country: UNCountry | None = None,
) -> TCCDestination:
    tcc = TCCDestination(
        name=name,
        tcc_region=region,
        tcc_index=tcc_index,
        un_country_id=un_country.id if un_country else None,
    )
    db.add(tcc)
    db.flush()
    return tcc


# --- Create trip with full relations ---


def test_create_trip_with_cities(admin_client: TestClient, db_session: Session) -> None:
    """Create trip with cities list."""
    country = _create_country(db_session)
    tcc = _create_tcc(db_session, un_country=country)
    db_session.commit()

    res = admin_client.post(
        "/api/v1/travels/trips",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-10",
            "destinations": [{"tcc_destination_id": tcc.id, "is_partial": False}],
            "cities": [
                {"name": "Prague", "is_partial": False},
                {"name": "Brno", "is_partial": True},
            ],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["cities"]) == 2
    assert data["cities"][0]["name"] == "Prague"
    assert data["cities"][1]["name"] == "Brno"
    assert data["cities"][1]["is_partial"] is True


def test_create_trip_with_participants(
    admin_client: TestClient, db_session: Session, admin_user: User
) -> None:
    """Create trip with participant IDs."""
    # Create another user
    other = User(email="friend@test.com", name="Friend", is_active=True)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    res = admin_client.post(
        "/api/v1/travels/trips",
        json={
            "start_date": "2026-07-01",
            "end_date": "2026-07-10",
            "participant_ids": [other.id],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["participants"]) == 1
    assert data["participants"][0]["name"] == "Friend"


def test_create_trip_invalid_participant_ignored(
    admin_client: TestClient, db_session: Session
) -> None:
    """Non-existent participant IDs are silently ignored."""
    res = admin_client.post(
        "/api/v1/travels/trips",
        json={
            "start_date": "2026-08-01",
            "participant_ids": [99999],
        },
    )
    assert res.status_code == 200
    assert res.json()["participants"] == []


# --- Update trip with destinations/cities/participants ---


def test_update_trip_destinations(admin_client: TestClient, db_session: Session) -> None:
    """Updating destinations replaces them."""
    c1 = _create_country(db_session, name="Alpha", iso2="AA", iso3="AAA", iso_num="001")
    c2 = _create_country(db_session, name="Beta", iso2="BB", iso3="BBB", iso_num="002")
    tcc1 = _create_tcc(db_session, name="City A", tcc_index=1, un_country=c1)
    tcc2 = _create_tcc(db_session, name="City B", tcc_index=2, un_country=c2)
    db_session.commit()

    # Create trip with tcc1
    res = admin_client.post(
        "/api/v1/travels/trips",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-10",
            "destinations": [{"tcc_destination_id": tcc1.id, "is_partial": False}],
        },
    )
    trip_id = res.json()["id"]

    # Update to tcc2
    res = admin_client.put(
        f"/api/v1/travels/trips/{trip_id}",
        json={
            "destinations": [{"tcc_destination_id": tcc2.id, "is_partial": True}],
        },
    )
    assert res.status_code == 200
    dests = res.json()["destinations"]
    assert len(dests) == 1
    assert dests[0]["name"] == "City B"
    assert dests[0]["is_partial"] is True


def test_update_trip_cities(admin_client: TestClient, db_session: Session) -> None:
    """Updating cities replaces the list."""
    res = admin_client.post(
        "/api/v1/travels/trips",
        json={
            "start_date": "2026-06-01",
            "cities": [{"name": "Prague", "is_partial": False}],
        },
    )
    trip_id = res.json()["id"]

    res = admin_client.put(
        f"/api/v1/travels/trips/{trip_id}",
        json={
            "cities": [
                {"name": "Brno", "is_partial": False},
                {"name": "Ostrava", "is_partial": True},
            ],
        },
    )
    assert res.status_code == 200
    cities = res.json()["cities"]
    assert len(cities) == 2
    assert cities[0]["name"] == "Brno"


def test_update_trip_participants(
    admin_client: TestClient, db_session: Session
) -> None:
    """Updating participants replaces the list."""
    user1 = User(email="p1@test.com", name="P1", is_active=True)
    user2 = User(email="p2@test.com", name="P2", is_active=True)
    db_session.add_all([user1, user2])
    db_session.commit()

    res = admin_client.post(
        "/api/v1/travels/trips",
        json={
            "start_date": "2026-09-01",
            "participant_ids": [user1.id],
        },
    )
    trip_id = res.json()["id"]

    res = admin_client.put(
        f"/api/v1/travels/trips/{trip_id}",
        json={"participant_ids": [user2.id]},
    )
    assert res.status_code == 200
    parts = res.json()["participants"]
    assert len(parts) == 1
    assert parts[0]["name"] == "P2"


# --- Users Options ---


def test_users_options(admin_client: TestClient, db_session: Session) -> None:
    """Users options returns non-admin users."""
    user = User(email="friend@test.com", name="Friend", nickname="frnd", is_active=True)
    db_session.add(user)
    db_session.commit()

    res = admin_client.get("/api/v1/travels/users-options")
    assert res.status_code == 200
    data = res.json()
    assert len(data["users"]) >= 1
    names = [u["name"] for u in data["users"]]
    assert "Friend" in names


# --- City Search ---


@patch("src.travels.trips_nominatim._search_nominatim", return_value=[])
def test_city_search_local(
    _mock_nominatim: object, admin_client: TestClient, db_session: Session
) -> None:
    """City search finds local DB cities first."""
    city = City(
        name="Prague",
        country="Czech Republic",
        country_code="CZ",
        lat=50.08,
        lng=14.44,
    )
    db_session.add(city)
    db_session.commit()

    res = admin_client.get("/api/v1/travels/cities-search", params={"q": "Prag"})
    assert res.status_code == 200
    data = res.json()
    assert any(r["name"] == "Prague" for r in data["results"])


@patch("src.travels.trips_nominatim._search_nominatim", return_value=[])
def test_city_search_with_country_filter(
    _mock_nominatim: object, admin_client: TestClient, db_session: Session
) -> None:
    """City search filters by country code."""
    db_session.add(City(name="Paris", country="France", country_code="FR", lat=48.85, lng=2.35))
    db_session.add(City(name="Paris", country="USA", country_code="US", lat=33.66, lng=-95.55))
    db_session.commit()

    res = admin_client.get(
        "/api/v1/travels/cities-search", params={"q": "Paris", "country_codes": "FR"}
    )
    assert res.status_code == 200
    results = res.json()["results"]
    assert all(r["country_code"] == "FR" for r in results)


# --- Holidays Endpoint ---


@patch("httpx.get")
def test_holidays_endpoint(mock_get: MagicMock, admin_client: TestClient) -> None:
    """GET /holidays returns parsed holiday data."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"date": "2026-01-01", "name": "New Year's Day", "localName": "Nový rok"},
        {"date": "2026-12-25", "name": "Christmas", "localName": "Vánoce"},
    ]
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    # Clear holidays cache to force fetch
    from src.travels.trips import _holidays_cache

    _holidays_cache.clear()

    res = admin_client.get("/api/v1/travels/holidays/2026/CZ")
    assert res.status_code == 200
    holidays = res.json()["holidays"]
    assert len(holidays) == 2
    assert holidays[0]["name"] == "New Year's Day"
    assert holidays[0]["local_name"] == "Nový rok"


@patch("httpx.get")
def test_holidays_not_found(mock_get: MagicMock, admin_client: TestClient) -> None:
    """GET /holidays returns empty for unknown country."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    from src.travels.trips import _holidays_cache

    _holidays_cache.clear()

    res = admin_client.get("/api/v1/travels/holidays/2026/XX")
    assert res.status_code == 200
    assert res.json()["holidays"] == []


@patch("httpx.get", side_effect=Exception("network error"))
def test_holidays_api_error(mock_get: MagicMock, admin_client: TestClient) -> None:
    """GET /holidays returns empty on API failure."""
    from src.travels.trips import _holidays_cache

    _holidays_cache.clear()

    res = admin_client.get("/api/v1/travels/holidays/2026/CZ")
    assert res.status_code == 200
    assert res.json()["holidays"] == []


# --- Helper functions ---


def test_compute_timezone_offset() -> None:
    from src.travels.trips import _compute_timezone_offset

    # Same timezone as CET
    offset = _compute_timezone_offset("Europe/Prague", date(2026, 6, 15))
    assert offset == 0.0

    # UTC is behind CET
    offset = _compute_timezone_offset("UTC", date(2026, 6, 15))
    assert offset is not None
    assert offset < 0

    # Invalid timezone
    offset = _compute_timezone_offset("Invalid/Zone", date(2026, 6, 15))
    assert offset is None


def test_vaccine_matches() -> None:
    from src.travels.trips import _vaccine_matches

    # Exact match
    assert _vaccine_matches("Hepatitis A", {"hepatitis a"}) is True

    # Case insensitive
    assert _vaccine_matches("Yellow Fever", {"yellow fever"}) is True

    # Combined vaccine covers individual
    assert _vaccine_matches("Hepatitis A", {"hepatitis a+b"}) is True
    assert _vaccine_matches("Hepatitis B", {"hepatitis a+b"}) is True

    # Parenthetical stripping
    assert _vaccine_matches("Polio (booster)", {"polio"}) is True

    # No match
    assert _vaccine_matches("Rabies", {"hepatitis a", "polio"}) is False

    # Empty set
    assert _vaccine_matches("Hepatitis A", set()) is False


def test_get_health_requirements() -> None:
    """Health requirements lookup for known/unknown countries."""
    from src.travels.trips import _get_health_requirements

    # Unknown country returns None
    assert _get_health_requirements("XX") is None

    # Known country (if health data loaded) - just test it doesn't crash
    result = _get_health_requirements("KE")  # Kenya likely in data
    # Either None (no data file) or a valid object
    if result is not None:
        assert hasattr(result, "vaccinations_required")
        assert hasattr(result, "malaria")


# --- Flight lookup with mock ---


@patch("src.travels.flights.settings")
@patch("httpx.get")
def test_flight_lookup_mocked(
    mock_get: MagicMock, mock_settings: MagicMock, admin_client: TestClient
) -> None:
    """Flight lookup with mocked AeroDataBox API."""
    mock_settings.aerodatabox_api_key = "test-key"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "departure": {
                "airport": {
                    "iata": "PRG",
                    "name": "Prague",
                    "countryCode": "CZ",
                    "municipalityName": "Prague",
                    "location": {"lat": 50.1, "lon": 14.26},
                },
                "scheduledTime": {"local": "2026-03-10 06:30+01:00"},
            },
            "arrival": {
                "airport": {
                    "iata": "IST",
                    "name": "Istanbul",
                    "countryCode": "TR",
                    "municipalityName": "Istanbul",
                    "location": {"lat": 40.98, "lon": 28.82},
                },
                "scheduledTime": {"local": "2026-03-10 10:15+03:00"},
            },
            "airline": {"name": "Turkish Airlines"},
            "aircraft": {"model": "Airbus A321"},
        }
    ]
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    res = admin_client.get(
        "/api/v1/travels/flights/lookup",
        params={"flight_number": "TK1770", "date": "2026-03-10"},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["legs"]) == 1
    leg = data["legs"][0]
    assert leg["departure_iata"] == "PRG"
    assert leg["arrival_iata"] == "IST"
    assert leg["departure_time"] == "06:30"
    assert leg["arrival_time"] == "10:15"
    assert leg["aircraft_type"] == "Airbus A321"


@patch("src.travels.flights.settings")
@patch("httpx.get")
def test_flight_lookup_204(
    mock_get: MagicMock, mock_settings: MagicMock, admin_client: TestClient
) -> None:
    """Flight lookup returns empty legs on 204 (no data)."""
    mock_settings.aerodatabox_api_key = "test-key"

    mock_resp = MagicMock()
    mock_resp.status_code = 204
    mock_get.return_value = mock_resp

    res = admin_client.get(
        "/api/v1/travels/flights/lookup",
        params={"flight_number": "XX999", "date": "2026-03-10"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["legs"] == []
    assert data["error"] is not None


@patch("src.travels.flights.settings")
@patch("httpx.get", side_effect=httpx.ConnectError("timeout"))
def test_flight_lookup_network_error(
    mock_get: MagicMock, mock_settings: MagicMock, admin_client: TestClient
) -> None:
    """Flight lookup returns error on network failure."""
    mock_settings.aerodatabox_api_key = "test-key"

    res = admin_client.get(
        "/api/v1/travels/flights/lookup",
        params={"flight_number": "TK1", "date": "2026-03-10"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["legs"] == []
    assert "failed" in data["error"].lower()


# --- Parse time helper ---


def test_parse_time() -> None:
    from src.travels.flights import _parse_time

    assert _parse_time(None) is None
    assert _parse_time("06:30") == "06:30"
    assert _parse_time("2026-03-10T06:30+01:00") == "06:30"
    assert _parse_time("2026-03-10 06:30+01:00") == "06:30"


def test_parse_date_from_datetime() -> None:
    from src.travels.flights import _parse_date_from_datetime

    assert _parse_date_from_datetime(None) is None
    assert _parse_date_from_datetime("2026-03-10 06:30+01:00") == "2026-03-10"
    assert _parse_date_from_datetime("2026-03-10T06:30+01:00") == "2026-03-10"
