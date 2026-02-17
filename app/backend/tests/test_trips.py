"""Tests for trip management and country-info endpoints."""

from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import TCCDestination, Trip, TripDestination, UNCountry


def _create_country(
    db: Session,
    *,
    name: str = "Testland",
    iso2: str = "TL",
    iso3: str = "TLD",
    iso_num: str = "999",
    continent: str = "Europe",
    socket_types: str | None = "C,F",
    voltage: str | None = "230V 50Hz",
    phone_code: str | None = "+99",
    driving_side: str | None = "right",
    emergency_number: str | None = "112",
    tap_water: str | None = "safe",
    currency_code: str | None = "EUR",
    capital_lat: float | None = 50.0,
    capital_lng: float | None = 14.0,
    timezone: str | None = "Europe/Prague",
    languages: str | None = "Testish",
    tipping: str | None = "10%",
    speed_limits: str | None = "50/90/130",
    visa_free_days: int | None = None,
    eu_roaming: bool | None = True,
) -> UNCountry:
    country = UNCountry(
        name=name,
        iso_alpha2=iso2,
        iso_alpha3=iso3,
        iso_numeric=iso_num,
        continent=continent,
        map_region_codes=iso2,
        socket_types=socket_types,
        voltage=voltage,
        phone_code=phone_code,
        driving_side=driving_side,
        emergency_number=emergency_number,
        tap_water=tap_water,
        currency_code=currency_code,
        capital_lat=capital_lat,
        capital_lng=capital_lng,
        timezone=timezone,
        languages=languages,
        tipping=tipping,
        speed_limits=speed_limits,
        visa_free_days=visa_free_days,
        eu_roaming=eu_roaming,
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


def _create_trip(
    db: Session,
    *,
    start: str = "2026-03-01",
    end: str | None = "2026-03-10",
    destinations: list[TCCDestination] | None = None,
) -> Trip:
    trip = Trip(
        start_date=date.fromisoformat(start),
        end_date=date.fromisoformat(end) if end else None,
    )
    db.add(trip)
    db.flush()

    for tcc in destinations or []:
        td = TripDestination(trip_id=trip.id, tcc_destination_id=tcc.id)
        db.add(td)

    db.commit()
    db.refresh(trip)
    return trip


# --- Trip CRUD tests ---


def test_get_trips_empty(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/travels/trips")
    assert response.status_code == 200
    data = response.json()
    assert data["trips"] == []
    assert data["total"] == 0


def test_get_trips_returns_trip(admin_client: TestClient, db_session: Session) -> None:
    country = _create_country(db_session)
    tcc = _create_tcc(db_session, un_country=country)
    _create_trip(db_session, destinations=[tcc])

    response = admin_client.get("/api/v1/travels/trips")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["trips"][0]["start_date"] == "2026-03-01"
    assert len(data["trips"][0]["destinations"]) == 1


def test_get_trips_requires_admin(client: TestClient) -> None:
    response = client.get("/api/v1/travels/trips")
    assert response.status_code in (401, 403)


def test_create_trip(admin_client: TestClient, db_session: Session) -> None:
    country = _create_country(db_session)
    tcc = _create_tcc(db_session, un_country=country)

    response = admin_client.post(
        "/api/v1/travels/trips",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-15",
            "destinations": [{"tcc_destination_id": tcc.id, "is_partial": False}],
            "cities": [{"name": "Test City", "is_partial": False}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == "2026-06-01"
    assert data["end_date"] == "2026-06-15"
    assert len(data["destinations"]) == 1


def test_create_trip_minimal(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/api/v1/travels/trips",
        json={"start_date": "2026-07-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == "2026-07-01"
    assert data["end_date"] is None


def test_get_single_trip(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    response = admin_client.get(f"/api/v1/travels/trips/{trip.id}")
    assert response.status_code == 200
    assert response.json()["id"] == trip.id


def test_get_trip_not_found(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/travels/trips/99999")
    assert response.status_code == 404


def test_update_trip(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    response = admin_client.put(
        f"/api/v1/travels/trips/{trip.id}",
        json={"description": "Updated description", "flights_count": 4},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["flights_count"] == 4


def test_update_trip_not_found(admin_client: TestClient) -> None:
    response = admin_client.put(
        "/api/v1/travels/trips/99999",
        json={"description": "Nope"},
    )
    assert response.status_code == 404


def test_delete_trip(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    response = admin_client.delete(f"/api/v1/travels/trips/{trip.id}")
    assert response.status_code == 200

    response = admin_client.get(f"/api/v1/travels/trips/{trip.id}")
    assert response.status_code == 404


def test_delete_trip_not_found(admin_client: TestClient) -> None:
    response = admin_client.delete("/api/v1/travels/trips/99999")
    assert response.status_code == 404


# --- TCC Options ---


def test_tcc_options(admin_client: TestClient, db_session: Session) -> None:
    country = _create_country(db_session)
    _create_tcc(db_session, name="Prague", un_country=country)
    db_session.commit()

    response = admin_client.get("/api/v1/travels/tcc-options")
    assert response.status_code == 200
    data = response.json()
    assert len(data["destinations"]) == 1
    assert data["destinations"][0]["name"] == "Prague"


# --- Country Info endpoint ---


@patch(
    "src.travels.trips._fetch_currency_rates",
    return_value={"EUR": 1.0, "CZK": 25.5, "USD": 1.08},
)
@patch(
    "src.travels.trips._fetch_weather",
    return_value={
        "avg_temp_c": 15.0,
        "min_temp_c": 8.0,
        "max_temp_c": 22.0,
        "avg_precipitation_mm": 2.5,
        "rainy_days": 7,
    },
)
@patch("src.travels.trips._fetch_sunrise_sunset", return_value=None)
@patch("src.travels.trips._fetch_holidays_for_country", return_value=[])
def test_country_info_returns_data(
    _mock_holidays: object,
    _mock_sunrise: object,
    _mock_weather: object,
    _mock_currency: object,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    country = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tcc = _create_tcc(db_session, name="Prague", un_country=country)
    trip = _create_trip(db_session, destinations=[tcc])

    response = admin_client.get(f"/api/v1/travels/trips/{trip.id}/country-info")
    assert response.status_code == 200
    data = response.json()
    assert len(data["countries"]) == 1

    c = data["countries"][0]
    assert c["country_name"] == "Czechia"
    assert c["iso_alpha2"] == "CZ"
    assert len(c["tcc_destinations"]) == 1
    assert c["tcc_destinations"][0]["name"] == "Prague"

    # Reference data
    assert c["socket_types"] == "C,F"
    assert c["voltage"] == "230V 50Hz"
    assert c["phone_code"] == "+99"
    assert c["driving_side"] == "right"
    assert c["emergency_number"] == "112"
    assert c["tap_water"] == "safe"
    assert c["languages"] == "Testish"
    assert c["tipping"] == "10%"
    assert c["speed_limits"] == "50/90/130"
    assert c["eu_roaming"] is True
    assert c["visa_free_days"] is None  # EU = unlimited

    # Adapter: C,F includes C (Czech standard) → no adapter needed
    assert c["adapter_needed"] is False

    # Currency
    assert c["currency"]["code"] == "EUR"
    assert c["currency"]["name"] == "Euro"
    assert c["currency"]["rates"]["CZK"] == 25.5

    # Weather
    assert c["weather"]["min_temp_c"] == 8.0
    assert c["weather"]["max_temp_c"] == 22.0
    assert c["weather"]["rainy_days"] == 7
    assert c["weather"]["month"] == "March"


@patch("src.travels.trips._fetch_currency_rates", return_value=None)
@patch(
    "src.travels.trips._fetch_weather",
    return_value={
        "avg_temp_c": None,
        "min_temp_c": None,
        "max_temp_c": None,
        "avg_precipitation_mm": None,
        "rainy_days": None,
    },
)
@patch("src.travels.trips._fetch_sunrise_sunset", return_value=None)
@patch("src.travels.trips._fetch_holidays_for_country", return_value=[])
def test_country_info_adapter_needed(
    _mock_holidays: object,
    _mock_sunrise: object,
    _mock_weather: object,
    _mock_currency: object,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    """Country with only G sockets (UK) should need an adapter."""
    country = _create_country(
        db_session,
        name="United Kingdom",
        iso2="GB",
        iso3="GBR",
        iso_num="826",
        socket_types="G",
        currency_code="GBP",
        eu_roaming=False,
        visa_free_days=180,
    )
    tcc = _create_tcc(db_session, name="London", un_country=country)
    trip = _create_trip(db_session, destinations=[tcc])

    response = admin_client.get(f"/api/v1/travels/trips/{trip.id}/country-info")
    assert response.status_code == 200

    c = response.json()["countries"][0]
    assert c["adapter_needed"] is True
    assert c["eu_roaming"] is False
    assert c["visa_free_days"] == 180


@patch("src.travels.trips._fetch_currency_rates", return_value=None)
@patch("src.travels.trips._fetch_sunrise_sunset", return_value=None)
@patch("src.travels.trips._fetch_holidays_for_country", return_value=[])
def test_country_info_multiple_countries(
    _mock_holidays: object,
    _mock_sunrise: object,
    _mock_currency: object,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    """Trip with destinations in two countries returns both."""
    c1 = _create_country(db_session, name="Alpha", iso2="AA", iso3="AAA", iso_num="001")
    c2 = _create_country(
        db_session,
        name="Beta",
        iso2="BB",
        iso3="BBB",
        iso_num="002",
        capital_lat=None,
        capital_lng=None,
    )
    tcc1 = _create_tcc(db_session, name="City A", tcc_index=1, un_country=c1)
    tcc2 = _create_tcc(db_session, name="City B", tcc_index=2, un_country=c2)
    trip = _create_trip(db_session, destinations=[tcc1, tcc2])

    response = admin_client.get(f"/api/v1/travels/trips/{trip.id}/country-info")
    assert response.status_code == 200
    data = response.json()
    assert len(data["countries"]) == 2

    names = [c["country_name"] for c in data["countries"]]
    assert "Alpha" in names
    assert "Beta" in names

    # Beta has no capital coords → no weather
    beta = next(c for c in data["countries"] if c["country_name"] == "Beta")
    assert beta["weather"] is None


def test_country_info_trip_not_found(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/travels/trips/99999/country-info")
    assert response.status_code == 404


def test_country_info_no_destinations(admin_client: TestClient, db_session: Session) -> None:
    """Trip with no destinations returns empty countries list."""
    trip = _create_trip(db_session)

    response = admin_client.get(f"/api/v1/travels/trips/{trip.id}/country-info")
    assert response.status_code == 200
    assert response.json()["countries"] == []


def test_country_info_requires_admin(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    response = client.get(f"/api/v1/travels/trips/{trip.id}/country-info")
    assert response.status_code in (401, 403)


@patch("src.travels.trips._fetch_currency_rates", return_value=None)
@patch("src.travels.trips._fetch_sunrise_sunset", return_value=None)
@patch("src.travels.trips._fetch_holidays_for_country", return_value=[])
def test_country_info_orphan_destination(
    _mock_holidays: object,
    _mock_sunrise: object,
    _mock_currency: object,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    """TCC destination without UN country (e.g. Kosovo) gets minimal card."""
    tcc = _create_tcc(db_session, name="Kosovo", tcc_index=50, un_country=None)
    trip = _create_trip(db_session, destinations=[tcc])

    response = admin_client.get(f"/api/v1/travels/trips/{trip.id}/country-info")
    assert response.status_code == 200
    data = response.json()
    assert len(data["countries"]) == 1

    c = data["countries"][0]
    assert c["country_name"] == "Kosovo"
    assert c["iso_alpha2"] == ""
    assert c["socket_types"] is None
    assert c["adapter_needed"] is None
    assert c["currency"] is None
    assert c["weather"] is None


# --- Helper function unit tests ---


def test_needs_adapter() -> None:
    from src.travels.trips import _needs_adapter

    # Czech sockets C,E → compatible
    assert _needs_adapter("C,E") is False
    assert _needs_adapter("C,F") is False
    assert _needs_adapter("E,F") is False

    # Only non-Czech sockets → adapter needed
    assert _needs_adapter("G") is True
    assert _needs_adapter("A,B") is True
    assert _needs_adapter("I") is True

    # Mixed with C or E → compatible
    assert _needs_adapter("A,B,C") is False
    assert _needs_adapter("G,E") is False

    # None → unknown
    assert _needs_adapter(None) is None
    assert _needs_adapter("") is None


def test_get_currency_name() -> None:
    from src.travels.trips import _get_currency_name

    assert _get_currency_name("EUR") == "Euro"
    assert _get_currency_name("USD") == "US Dollar"
    assert _get_currency_name("CZK") == "Czech Koruna"
    assert _get_currency_name("GBP") == "Pound Sterling"
    assert _get_currency_name("XYZ") is None


# --- Vacation calculator unit tests ---


def test_vacation_weekday_trip() -> None:
    """Full weekday trip (Mon-Fri) with default departure/arrival = 5 days."""
    from src.travels.vacation import count_vacation_days

    # Mon 2026-03-02 to Fri 2026-03-06
    result = count_vacation_days(
        date(2026, 3, 2), date(2026, 3, 6), set()
    )
    assert result == 5.0


def test_vacation_weekend_exclusion() -> None:
    """Trip spanning a weekend skips Sat/Sun."""
    from src.travels.vacation import count_vacation_days

    # Thu 2026-03-05 to Tue 2026-03-10 = Thu,Fri,(Sat,Sun),Mon,Tue = 4 days
    result = count_vacation_days(
        date(2026, 3, 5), date(2026, 3, 10), set()
    )
    assert result == 4.0


def test_vacation_holiday_exclusion() -> None:
    """Holiday on a weekday is excluded."""
    from src.travels.vacation import count_vacation_days

    # Mon-Fri, with Wednesday as a holiday
    holidays = {date(2026, 3, 4)}  # Wednesday
    result = count_vacation_days(
        date(2026, 3, 2), date(2026, 3, 6), holidays
    )
    assert result == 4.0


def test_vacation_midday_departure() -> None:
    """Midday departure = half day on departure."""
    from src.travels.vacation import count_vacation_days

    # Mon-Wed, midday departure
    result = count_vacation_days(
        date(2026, 3, 2), date(2026, 3, 4), set(),
        departure_type="midday", arrival_type="evening",
    )
    # Mon(0.5) + Tue(1.0) + Wed(1.0) = 2.5
    assert result == 2.5


def test_vacation_midday_arrival() -> None:
    """Midday arrival = half day on arrival."""
    from src.travels.vacation import count_vacation_days

    # Mon-Wed, midday arrival
    result = count_vacation_days(
        date(2026, 3, 2), date(2026, 3, 4), set(),
        departure_type="morning", arrival_type="midday",
    )
    # Mon(1.0) + Tue(1.0) + Wed(0.5) = 2.5
    assert result == 2.5


def test_vacation_evening_departure() -> None:
    """Evening departure = 0 days on departure day."""
    from src.travels.vacation import count_vacation_days

    # Mon-Tue, evening departure
    result = count_vacation_days(
        date(2026, 3, 2), date(2026, 3, 3), set(),
        departure_type="evening", arrival_type="evening",
    )
    # Mon(0.0) + Tue(1.0) = 1.0
    assert result == 1.0


def test_vacation_single_day_full() -> None:
    """Single-day trip morning->evening = 1 full day."""
    from src.travels.vacation import count_vacation_days

    result = count_vacation_days(
        date(2026, 3, 2), date(2026, 3, 2), set(),
        departure_type="morning", arrival_type="evening",
    )
    assert result == 1.0


def test_vacation_single_day_half() -> None:
    """Single-day trip morning->midday = 0.5 day."""
    from src.travels.vacation import count_vacation_days

    result = count_vacation_days(
        date(2026, 3, 2), date(2026, 3, 2), set(),
        departure_type="morning", arrival_type="midday",
    )
    assert result == 0.5


def test_vacation_single_day_weekend() -> None:
    """Single-day trip on Saturday = 0 days."""
    from src.travels.vacation import count_vacation_days

    # Sat 2026-03-07
    result = count_vacation_days(
        date(2026, 3, 7), date(2026, 3, 7), set()
    )
    assert result == 0.0


# --- Vacation summary endpoint tests ---


@patch("src.travels.trips._fetch_holidays_raw", return_value=[])
def test_vacation_summary_regular_trips(
    _mock_holidays: object,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    """Regular trips are counted in vacation summary."""
    # Past trip: Mon-Fri (5 weekdays)
    trip = Trip(
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 9),
        trip_type="regular",
        departure_type="morning",
        arrival_type="evening",
    )
    db_session.add(trip)
    db_session.commit()

    response = admin_client.get("/api/v1/travels/vacation-summary?year=2026")
    assert response.status_code == 200
    data = response.json()
    assert data["annual_days"] == 30
    assert data["used_days"] == 5.0
    assert data["remaining_days"] == 25.0


@patch("src.travels.trips._fetch_holidays_raw", return_value=[])
def test_vacation_summary_work_trips_excluded(
    _mock_holidays: object,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    """Work trips don't consume vacation days."""
    trip = Trip(
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 9),
        trip_type="work",
    )
    db_session.add(trip)
    db_session.commit()

    response = admin_client.get("/api/v1/travels/vacation-summary?year=2026")
    assert response.status_code == 200
    data = response.json()
    assert data["used_days"] == 0.0
    assert data["planned_days"] == 0.0
    assert data["remaining_days"] == 30.0


@patch("src.travels.trips._fetch_holidays_raw", return_value=[])
def test_vacation_summary_future_as_planned(
    _mock_holidays: object,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    """Future trips go into planned_days, not used_days."""
    trip = Trip(
        start_date=date(2026, 12, 21),
        end_date=date(2026, 12, 25),
        trip_type="regular",
        departure_type="morning",
        arrival_type="evening",
    )
    db_session.add(trip)
    db_session.commit()

    response = admin_client.get("/api/v1/travels/vacation-summary?year=2026")
    assert response.status_code == 200
    data = response.json()
    assert data["used_days"] == 0.0
    assert data["planned_days"] == 5.0
    assert data["remaining_days"] == 25.0


# --- Trip CRUD with departure/arrival types ---


def test_create_trip_with_departure_arrival(
    admin_client: TestClient,
) -> None:
    """Trip creation accepts departure/arrival types."""
    response = admin_client.post(
        "/api/v1/travels/trips",
        json={
            "start_date": "2026-08-01",
            "end_date": "2026-08-10",
            "departure_type": "midday",
            "arrival_type": "morning",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["departure_type"] == "midday"
    assert data["arrival_type"] == "morning"


def test_update_trip_departure_arrival(
    admin_client: TestClient, db_session: Session,
) -> None:
    """Trip update can change departure/arrival types."""
    trip = _create_trip(db_session)
    response = admin_client.put(
        f"/api/v1/travels/trips/{trip.id}",
        json={"departure_type": "evening", "arrival_type": "midday"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["departure_type"] == "evening"
    assert data["arrival_type"] == "midday"


def test_trip_default_departure_arrival(admin_client: TestClient) -> None:
    """Trips default to morning departure and evening arrival."""
    response = admin_client.post(
        "/api/v1/travels/trips",
        json={"start_date": "2026-09-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["departure_type"] == "morning"
    assert data["arrival_type"] == "evening"
