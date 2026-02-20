"""Tests for travels data endpoints (map data, countries, cities, flights)."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import (
    Airport,
    City,
    Flight,
    Microstate,
    NMRegion,
    TCCDestination,
    Trip,
    TripCity,
    TripDestination,
    UNCountry,
    Visit,
)

BASE = "/api/v1/travels"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_country(
    db: Session,
    *,
    name: str = "Testland",
    iso2: str = "TL",
    iso3: str = "TLD",
    iso_num: str = "999",
    continent: str = "Europe",
    map_region_codes: str | None = None,
) -> UNCountry:
    country = UNCountry(
        name=name,
        iso_alpha2=iso2,
        iso_alpha3=iso3,
        iso_numeric=iso_num,
        continent=continent,
        map_region_codes=map_region_codes or iso_num,
    )
    db.add(country)
    db.flush()
    return country


def _create_tcc(
    db: Session,
    *,
    name: str = "Testland",
    region: str = "EUROPE & MEDITERRANEAN",
    tcc_index: int = 1,
    un_country: UNCountry | None = None,
    map_region_code: str | None = None,
    iso_alpha2: str | None = None,
) -> TCCDestination:
    dest = TCCDestination(
        name=name,
        tcc_region=region,
        tcc_index=tcc_index,
        un_country_id=un_country.id if un_country else None,
        map_region_code=map_region_code,
        iso_alpha2=iso_alpha2,
    )
    db.add(dest)
    db.flush()
    return dest


def _create_visit(
    db: Session, tcc: TCCDestination, *, visit_date: date | None = None
) -> Visit:
    visit = Visit(tcc_destination_id=tcc.id, first_visit_date=visit_date)
    db.add(visit)
    db.flush()
    return visit


def _create_trip(
    db: Session,
    *,
    start: date = date(2024, 6, 1),
    end: date | None = date(2024, 6, 10),
) -> Trip:
    trip = Trip(start_date=start, end_date=end, trip_type="regular")
    db.add(trip)
    db.flush()
    return trip


def _create_airport(
    db: Session,
    iata: str,
    name: str | None = None,
    country_code: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> Airport:
    airport = Airport(
        iata_code=iata,
        name=name,
        country_code=country_code,
        latitude=lat,
        longitude=lng,
    )
    db.add(airport)
    db.flush()
    return airport


# ---------------------------------------------------------------------------
# Empty DB: all endpoints return proper empty structures
# ---------------------------------------------------------------------------


def test_data_empty(client: TestClient) -> None:
    res = client.get(f"{BASE}/data")
    assert res.status_code == 200
    data = res.json()
    assert data["stats"]["un_visited"] == 0
    assert data["stats"]["un_total"] == 0
    assert data["stats"]["tcc_visited"] == 0
    assert data["stats"]["tcc_total"] == 0
    assert data["stats"]["nm_visited"] == 0
    assert data["stats"]["nm_total"] == 0
    assert data["visited_map_regions"] == {}
    assert data["visited_countries"] == []
    assert data["microstates"] == []
    assert data["un_countries"] == []
    assert data["tcc_destinations"] == []
    assert data["nm_regions"] == []


def test_map_data_empty(client: TestClient) -> None:
    res = client.get(f"{BASE}/map-data")
    assert res.status_code == 200
    data = res.json()
    assert data["stats"]["un_visited"] == 0
    assert data["stats"]["un_total"] == 0
    assert data["visited_map_regions"] == {}
    assert data["visit_counts"] == {}
    assert data["region_names"] == {}
    assert data["visited_countries"] == []
    assert data["microstates"] == []


def test_un_countries_empty(client: TestClient) -> None:
    res = client.get(f"{BASE}/un-countries")
    assert res.status_code == 200
    assert res.json()["countries"] == []


def test_tcc_destinations_empty(client: TestClient) -> None:
    res = client.get(f"{BASE}/tcc-destinations")
    assert res.status_code == 200
    assert res.json()["destinations"] == []


def test_map_cities_empty(client: TestClient) -> None:
    res = client.get(f"{BASE}/map-cities")
    assert res.status_code == 200
    assert res.json()["cities"] == []


def test_map_flights_empty(client: TestClient) -> None:
    res = client.get(f"{BASE}/map-flights")
    assert res.status_code == 200
    data = res.json()
    assert data["airports"] == []
    assert data["routes"] == []
    assert data["country_regions"] == {}


# ---------------------------------------------------------------------------
# /data with seeded data
# ---------------------------------------------------------------------------


def test_data_stats_and_visited(client: TestClient, db_session: Session) -> None:
    """Seeded UN countries and TCC destinations produce correct stats."""
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tr = _create_country(db_session, name="Turkey", iso2="TR", iso3="TUR", iso_num="792")
    tcc_cz = _create_tcc(db_session, name="Czechia", tcc_index=1, un_country=cz)
    tcc_tr = _create_tcc(db_session, name="Turkey", tcc_index=2, un_country=tr)
    # Only Czechia visited
    _create_visit(db_session, tcc_cz, visit_date=date(2020, 3, 15))
    _create_visit(db_session, tcc_tr)  # no date = not visited
    db_session.commit()

    res = client.get(f"{BASE}/data")
    assert res.status_code == 200
    data = res.json()

    assert data["stats"]["un_total"] == 2
    assert data["stats"]["un_visited"] == 1
    assert data["stats"]["tcc_total"] == 2
    assert data["stats"]["tcc_visited"] == 1

    # Map regions: only Czechia region code present
    assert "203" in data["visited_map_regions"]
    assert "792" not in data["visited_map_regions"]

    # Visited countries list
    assert "Czechia" in data["visited_countries"]
    assert "Turkey" not in data["visited_countries"]

    # UN countries list: both present, only Czechia has visit_date
    un_names = {c["name"]: c for c in data["un_countries"]}
    assert un_names["Czechia"]["visit_date"] == "2020-03-15"
    assert un_names["Turkey"]["visit_date"] is None

    # TCC destinations list
    tcc_names = {d["name"]: d for d in data["tcc_destinations"]}
    assert tcc_names["Czechia"]["visit_date"] == "2020-03-15"
    assert tcc_names["Turkey"]["visit_date"] is None


def test_data_includes_microstates(client: TestClient, db_session: Session) -> None:
    ms = Microstate(name="Monaco", longitude=7.42, latitude=43.73, map_region_code="MCO")
    db_session.add(ms)
    db_session.commit()

    res = client.get(f"{BASE}/data")
    data = res.json()
    assert len(data["microstates"]) == 1
    assert data["microstates"][0]["name"] == "Monaco"
    assert data["microstates"][0]["longitude"] == 7.42


def test_data_includes_nm_regions(client: TestClient, db_session: Session) -> None:
    nm = NMRegion(name="Bohemia", country="Czechia", visited=True, first_visited_year=2020)
    db_session.add(nm)
    db_session.commit()

    res = client.get(f"{BASE}/data")
    data = res.json()
    assert data["stats"]["nm_total"] == 1
    assert data["stats"]["nm_visited"] == 1
    assert len(data["nm_regions"]) == 1
    assert data["nm_regions"][0]["name"] == "Bohemia"
    assert data["nm_regions"][0]["first_visited_year"] == 2020


# ---------------------------------------------------------------------------
# /map-data with seeded data
# ---------------------------------------------------------------------------


def test_map_data_visit_counts(client: TestClient, db_session: Session) -> None:
    """Map data includes region visit counts from trip destinations."""
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tcc_cz = _create_tcc(db_session, name="Czechia", tcc_index=1, un_country=cz)
    _create_visit(db_session, tcc_cz, visit_date=date(2020, 3, 15))

    # Two trips that include Czechia
    trip1 = _create_trip(db_session, start=date(2020, 3, 15), end=date(2020, 3, 20))
    trip2 = _create_trip(db_session, start=date(2023, 7, 1), end=date(2023, 7, 10))
    db_session.add(TripDestination(trip_id=trip1.id, tcc_destination_id=tcc_cz.id))
    db_session.add(TripDestination(trip_id=trip2.id, tcc_destination_id=tcc_cz.id))
    db_session.commit()

    res = client.get(f"{BASE}/map-data")
    assert res.status_code == 200
    data = res.json()

    assert data["stats"]["un_visited"] == 1
    assert data["stats"]["un_total"] == 1
    assert "203" in data["visited_map_regions"]
    assert data["visit_counts"]["203"] == 2
    assert data["region_names"]["203"] == "Czechia"
    assert "Czechia" in data["visited_countries"]


# ---------------------------------------------------------------------------
# /un-countries
# ---------------------------------------------------------------------------


def test_un_countries_with_data(client: TestClient, db_session: Session) -> None:
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    de = _create_country(
        db_session, name="Germany", iso2="DE", iso3="DEU", iso_num="276", continent="Europe"
    )
    tcc_cz = _create_tcc(db_session, name="Czechia", tcc_index=1, un_country=cz, iso_alpha2="CZ")
    tcc_de = _create_tcc(db_session, name="Germany", tcc_index=2, un_country=de, iso_alpha2="DE")
    _create_visit(db_session, tcc_cz, visit_date=date(2020, 3, 15))
    _create_visit(db_session, tcc_de)  # not visited
    db_session.commit()

    res = client.get(f"{BASE}/un-countries")
    assert res.status_code == 200
    countries = {c["name"]: c for c in res.json()["countries"]}
    assert len(countries) == 2

    assert countries["Czechia"]["visit_date"] == "2020-03-15"
    assert countries["Czechia"]["visit_count"] == 0  # no trip destinations
    assert countries["Germany"]["visit_date"] is None


def test_un_countries_visit_count_from_trips(
    client: TestClient, db_session: Session
) -> None:
    """Trip destinations increase visit_count for /un-countries."""
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tcc_cz = _create_tcc(db_session, name="Czechia", tcc_index=1, un_country=cz)
    _create_visit(db_session, tcc_cz, visit_date=date(2020, 3, 15))

    trip = _create_trip(db_session, start=date(2020, 3, 15), end=date(2020, 3, 20))
    db_session.add(TripDestination(trip_id=trip.id, tcc_destination_id=tcc_cz.id))
    db_session.commit()

    res = client.get(f"{BASE}/un-countries")
    countries = {c["name"]: c for c in res.json()["countries"]}
    assert countries["Czechia"]["visit_count"] == 1


# ---------------------------------------------------------------------------
# /tcc-destinations
# ---------------------------------------------------------------------------


def test_tcc_destinations_with_data(client: TestClient, db_session: Session) -> None:
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tcc_cz = _create_tcc(db_session, name="Czechia", tcc_index=1, un_country=cz)
    tcc_ko = _create_tcc(
        db_session, name="Kosovo", region="EUROPE & MEDITERRANEAN", tcc_index=2,
        map_region_code="XKX",
    )
    _create_visit(db_session, tcc_cz, visit_date=date(2020, 3, 15))
    _create_visit(db_session, tcc_ko)  # not visited
    db_session.commit()

    res = client.get(f"{BASE}/tcc-destinations")
    assert res.status_code == 200
    dests = {d["name"]: d for d in res.json()["destinations"]}
    assert len(dests) == 2
    assert dests["Czechia"]["visit_date"] == "2020-03-15"
    assert dests["Kosovo"]["visit_date"] is None


def test_tcc_destinations_visit_count(client: TestClient, db_session: Session) -> None:
    """Trip destinations increase visit_count on /tcc-destinations."""
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tcc_cz = _create_tcc(db_session, name="Czechia", tcc_index=1, un_country=cz)
    _create_visit(db_session, tcc_cz, visit_date=date(2020, 3, 15))

    trip = _create_trip(db_session, start=date(2020, 3, 15), end=date(2020, 3, 20))
    db_session.add(TripDestination(trip_id=trip.id, tcc_destination_id=tcc_cz.id))
    db_session.commit()

    res = client.get(f"{BASE}/tcc-destinations")
    dests = {d["name"]: d for d in res.json()["destinations"]}
    assert dests["Czechia"]["visit_count"] == 1


# ---------------------------------------------------------------------------
# /map-cities
# ---------------------------------------------------------------------------


def test_map_cities_returns_visited_cities(
    client: TestClient, db_session: Session
) -> None:
    """Cities linked to visited trips appear in map-cities response."""
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tcc_cz = _create_tcc(db_session, name="Czechia", tcc_index=1, un_country=cz, iso_alpha2="CZ")
    _create_visit(db_session, tcc_cz, visit_date=date(2020, 3, 15))

    trip = _create_trip(db_session, start=date(2020, 3, 15), end=date(2020, 3, 20))
    db_session.add(TripDestination(trip_id=trip.id, tcc_destination_id=tcc_cz.id))

    city = City(name="Prague", country_code="CZ", lat=50.08, lng=14.44)
    db_session.add(city)
    db_session.flush()

    db_session.add(TripCity(trip_id=trip.id, name="Prague", city_id=city.id, is_partial=False))
    db_session.commit()

    res = client.get(f"{BASE}/map-cities")
    assert res.status_code == 200
    cities = res.json()["cities"]
    assert len(cities) == 1
    assert cities[0]["name"] == "Prague"
    assert cities[0]["lat"] == 50.08
    assert cities[0]["lng"] == 14.44
    assert cities[0]["is_partial"] is False


def test_map_cities_excludes_unvisited(client: TestClient, db_session: Session) -> None:
    """Cities on future trips (visit_date in future) are not returned."""
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tcc_cz = _create_tcc(db_session, name="Czechia", tcc_index=1, un_country=cz, iso_alpha2="CZ")
    # Visit date far in the future
    _create_visit(db_session, tcc_cz, visit_date=date(2099, 1, 1))

    trip = _create_trip(db_session, start=date(2099, 1, 1), end=date(2099, 1, 10))
    db_session.add(TripDestination(trip_id=trip.id, tcc_destination_id=tcc_cz.id))

    city = City(name="Prague", country_code="CZ", lat=50.08, lng=14.44)
    db_session.add(city)
    db_session.flush()
    db_session.add(TripCity(trip_id=trip.id, name="Prague", city_id=city.id))
    db_session.commit()

    res = client.get(f"{BASE}/map-cities")
    assert res.json()["cities"] == []


# ---------------------------------------------------------------------------
# /map-flights
# ---------------------------------------------------------------------------


def test_map_flights_with_data(client: TestClient, db_session: Session) -> None:
    """Past flights produce airports, routes, and country_regions."""
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    tr = _create_country(db_session, name="Turkey", iso2="TR", iso3="TUR", iso_num="792")

    trip = _create_trip(db_session, start=date(2024, 6, 1), end=date(2024, 6, 10))
    prg = _create_airport(db_session, "PRG", "Prague", "CZ", 50.1, 14.26)
    ist = _create_airport(db_session, "IST", "Istanbul", "TR", 40.98, 28.82)

    db_session.add(
        Flight(
            trip_id=trip.id,
            flight_date=date(2024, 6, 1),
            flight_number="TK1770",
            departure_airport_id=prg.id,
            arrival_airport_id=ist.id,
        )
    )
    db_session.commit()

    res = client.get(f"{BASE}/map-flights")
    assert res.status_code == 200
    data = res.json()

    assert len(data["airports"]) == 2
    iatas = {a["iata_code"] for a in data["airports"]}
    assert iatas == {"PRG", "IST"}

    # Flights count per airport (1 dep for PRG, 1 arr for IST)
    by_iata = {a["iata_code"]: a for a in data["airports"]}
    assert by_iata["PRG"]["flights_count"] == 1
    assert by_iata["IST"]["flights_count"] == 1

    assert len(data["routes"]) == 1
    assert data["routes"][0]["count"] == 1

    # Country region mapping
    assert data["country_regions"]["203"] == 1
    assert data["country_regions"]["792"] == 1


def test_map_flights_excludes_future(client: TestClient, db_session: Session) -> None:
    """Flights with future dates are excluded from map-flights."""
    trip = _create_trip(db_session, start=date(2099, 1, 1), end=date(2099, 1, 10))
    prg = _create_airport(db_session, "PRG", "Prague", "CZ", 50.1, 14.26)
    ist = _create_airport(db_session, "IST", "Istanbul", "TR", 40.98, 28.82)

    db_session.add(
        Flight(
            trip_id=trip.id,
            flight_date=date(2099, 1, 5),
            flight_number="TK1770",
            departure_airport_id=prg.id,
            arrival_airport_id=ist.id,
        )
    )
    db_session.commit()

    res = client.get(f"{BASE}/map-flights")
    data = res.json()
    assert data["airports"] == []
    assert data["routes"] == []


def test_map_flights_route_normalization(client: TestClient, db_session: Session) -> None:
    """Two flights A->B and B->A produce a single normalized route with count=2."""
    trip = _create_trip(db_session)
    prg = _create_airport(db_session, "PRG", "Prague", "CZ", 50.1, 14.26)
    ist = _create_airport(db_session, "IST", "Istanbul", "TR", 40.98, 28.82)

    db_session.add(
        Flight(
            trip_id=trip.id,
            flight_date=date(2024, 6, 1),
            flight_number="TK1",
            departure_airport_id=prg.id,
            arrival_airport_id=ist.id,
        )
    )
    db_session.add(
        Flight(
            trip_id=trip.id,
            flight_date=date(2024, 6, 5),
            flight_number="TK2",
            departure_airport_id=ist.id,
            arrival_airport_id=prg.id,
        )
    )
    db_session.commit()

    res = client.get(f"{BASE}/map-flights")
    routes = res.json()["routes"]
    assert len(routes) == 1
    assert routes[0]["count"] == 2
    # Alphabetically: IST < PRG
    assert routes[0]["from_iata"] == "IST"
    assert routes[0]["to_iata"] == "PRG"


# ---------------------------------------------------------------------------
# PATCH /un-countries/{name}/activities
# ---------------------------------------------------------------------------


def test_update_activities_success(admin_client: TestClient, db_session: Session) -> None:
    _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    db_session.commit()

    res = admin_client.patch(
        f"{BASE}/un-countries/Czechia/activities",
        json={"driving_type": "rental", "drone_flown": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Czechia"
    assert data["driving_type"] == "rental"
    assert data["drone_flown"] is True

    # Verify persisted
    country = db_session.query(UNCountry).filter(UNCountry.name == "Czechia").first()
    assert country is not None
    assert country.driving_type == "rental"
    assert country.drone_flown is True


def test_update_activities_not_found(admin_client: TestClient) -> None:
    res = admin_client.patch(
        f"{BASE}/un-countries/Narnia/activities",
        json={"driving_type": None, "drone_flown": None},
    )
    assert res.status_code == 404


def test_update_activities_requires_admin(client: TestClient, db_session: Session) -> None:
    """Non-admin client gets 401 on PATCH activities."""
    _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    db_session.commit()

    res = client.patch(
        f"{BASE}/un-countries/Czechia/activities",
        json={"driving_type": "own", "drone_flown": False},
    )
    assert res.status_code == 401


def test_update_activities_clears_values(admin_client: TestClient, db_session: Session) -> None:
    """Setting driving_type and drone_flown to None clears the fields."""
    cz = _create_country(db_session, name="Czechia", iso2="CZ", iso3="CZE", iso_num="203")
    cz.driving_type = "rental"
    cz.drone_flown = True
    db_session.commit()

    res = admin_client.patch(
        f"{BASE}/un-countries/Czechia/activities",
        json={"driving_type": None, "drone_flown": None},
    )
    assert res.status_code == 200
    assert res.json()["driving_type"] is None
    assert res.json()["drone_flown"] is None
