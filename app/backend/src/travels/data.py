from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from ..auth.session import get_admin_user
from ..database import get_db
from ..models import (
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
    User,
    Visit,
)
from .models import (
    CityMarkerData,
    FlightMapAirport,
    FlightMapData,
    FlightMapRoute,
    MapCitiesResponse,
    MapData,
    MicrostateData,
    NMRegionData,
    TCCDestinationData,
    TCCDestinationsResponse,
    TravelData,
    TravelStats,
    UNCountriesResponse,
    UNCountryActivityUpdate,
    UNCountryData,
)

router = APIRouter()


@router.get("/data", response_model=TravelData)
def get_travel_data(db: Session = Depends(get_db)) -> TravelData:
    """Get travel statistics and visited map regions for the map."""

    # Count UN countries
    un_total = db.query(func.count(UNCountry.id)).scalar() or 0

    # Count visited UN countries (those with at least one visited TCC destination)
    un_visited = (
        db.query(func.count(func.distinct(TCCDestination.un_country_id)))
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(TCCDestination.un_country_id.isnot(None))
        .filter(Visit.first_visit_date.isnot(None))
        .scalar()
        or 0
    )

    # Count TCC destinations
    tcc_total = db.query(func.count(TCCDestination.id)).scalar() or 0
    tcc_visited = (
        db.query(func.count(Visit.id)).filter(Visit.first_visit_date.isnot(None)).scalar() or 0
    )

    # Get all map region codes with their first visit dates
    visited_map_regions: dict[str, date] = {}
    visited_countries: list[str] = []

    # Get visited UN countries with earliest visit date
    visited_un_data = (
        db.query(UNCountry, func.min(Visit.first_visit_date).label("first_visit"))
        .join(TCCDestination, TCCDestination.un_country_id == UNCountry.id)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(Visit.first_visit_date.isnot(None))
        .group_by(UNCountry.id)
        .all()
    )

    for country, first_visit in visited_un_data:
        visited_countries.append(country.name)
        # map_region_codes is comma-separated
        for code in country.map_region_codes.split(","):
            code = code.strip()
            if code and first_visit:
                # Keep earliest date if region already exists
                if code not in visited_map_regions or first_visit < visited_map_regions[code]:
                    visited_map_regions[code] = first_visit

    # Get map regions from TCC destinations with their own polygon (e.g., Kosovo, Somaliland)
    visited_tcc_with_polygon = (
        db.query(TCCDestination, Visit.first_visit_date)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(
            TCCDestination.map_region_code.isnot(None),
            TCCDestination.un_country_id.is_(None),  # Only non-UN territories
            Visit.first_visit_date.isnot(None),
        )
        .all()
    )

    for dest, first_visit in visited_tcc_with_polygon:
        if dest.map_region_code and first_visit:
            code = dest.map_region_code
            if code not in visited_map_regions or first_visit < visited_map_regions[code]:
                visited_map_regions[code] = first_visit
            visited_countries.append(dest.name)

    # Get all microstates
    microstates = db.query(Microstate).all()
    microstates_data = [
        MicrostateData(
            name=m.name,
            longitude=m.longitude,
            latitude=m.latitude,
            map_region_code=m.map_region_code,
        )
        for m in microstates
    ]

    # Convert dates to ISO strings
    visited_map_regions_iso = {code: d.isoformat() for code, d in visited_map_regions.items()}

    # Get all UN countries with their earliest visit date
    all_un_countries = db.query(UNCountry).order_by(UNCountry.continent, UNCountry.name).all()
    un_visit_dates: dict[int, date] = {}
    for country, first_visit in visited_un_data:
        un_visit_dates[country.id] = first_visit

    un_countries_data = [
        UNCountryData(
            name=c.name,
            continent=c.continent,
            visit_date=un_visit_dates[c.id].isoformat() if c.id in un_visit_dates else None,
            visit_count=0,  # Deprecated endpoint, count not used
        )
        for c in all_un_countries
    ]

    # Get all TCC destinations with their visit dates
    all_tcc = (
        db.query(TCCDestination, Visit.first_visit_date)
        .outerjoin(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .order_by(TCCDestination.tcc_region, TCCDestination.name)
        .all()
    )

    tcc_destinations_data = [
        TCCDestinationData(
            name=dest.name,
            region=dest.tcc_region,
            visit_date=visit_date.isoformat() if visit_date else None,
            visit_count=0,  # Deprecated endpoint, count not used
        )
        for dest, visit_date in all_tcc
    ]

    # Get NM stats and regions
    nm_total = db.query(func.count(NMRegion.id)).scalar() or 0
    nm_visited = db.query(func.count(NMRegion.id)).filter(NMRegion.visited.is_(True)).scalar() or 0

    all_nm = db.query(NMRegion).order_by(NMRegion.country, NMRegion.name).all()

    nm_regions_data = [
        NMRegionData(
            name=r.name,
            country=r.country,
            first_visited_year=r.first_visited_year,
            last_visited_year=r.last_visited_year,
        )
        for r in all_nm
    ]

    return TravelData(
        stats=TravelStats(
            un_visited=un_visited,
            un_total=un_total,
            tcc_visited=tcc_visited,
            tcc_total=tcc_total,
            nm_visited=nm_visited,
            nm_total=nm_total,
        ),
        visited_map_regions=visited_map_regions_iso,
        visited_countries=sorted(visited_countries),
        microstates=microstates_data,
        un_countries=un_countries_data,
        tcc_destinations=tcc_destinations_data,
        nm_regions=nm_regions_data,
    )


@router.get("/map-data", response_model=MapData)
def get_map_data(db: Session = Depends(get_db)) -> MapData:
    """Get map data: stats, visited regions, and microstates (fast, ~50 items)."""

    today = date.today()

    # Visited filter: destination has first_visit_date <= today
    # This allows location check-in to immediately update counters
    # (check-in sets first_visit_date to today for matching destinations)

    # Count UN countries
    un_total = db.query(func.count(UNCountry.id)).scalar() or 0

    # Count visited UN countries (those with first_visit_date <= today)
    un_visited = (
        db.query(func.count(func.distinct(TCCDestination.un_country_id)))
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(TCCDestination.un_country_id.isnot(None))
        .filter(Visit.first_visit_date <= today)
        .scalar()
        or 0
    )

    # Count planned UN countries (first_visit_date > today, i.e., future trips)
    un_planned = (
        db.query(func.count(func.distinct(TCCDestination.un_country_id)))
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(TCCDestination.un_country_id.isnot(None))
        .filter(Visit.first_visit_date > today)
        .scalar()
        or 0
    )

    # Count TCC destinations
    tcc_total = db.query(func.count(TCCDestination.id)).scalar() or 0
    tcc_visited = (
        db.query(func.count(Visit.id)).filter(Visit.first_visit_date <= today).scalar() or 0
    )

    # Count planned TCC destinations (first_visit_date > today)
    tcc_planned = (
        db.query(func.count(Visit.id)).filter(Visit.first_visit_date > today).scalar() or 0
    )

    # Get NM stats
    nm_total = db.query(func.count(NMRegion.id)).scalar() or 0
    nm_visited = db.query(func.count(NMRegion.id)).filter(NMRegion.visited.is_(True)).scalar() or 0

    # Get all map region codes with their first visit dates and trip counts
    visited_map_regions: dict[str, date] = {}
    visit_counts: dict[str, int] = {}
    visited_countries: list[str] = []

    # Count trips per TCC destination (for visit_counts display)
    # Trip counts use start_date - once trip starts, it counts
    tcc_trip_counts_query = (
        db.query(
            TripDestination.tcc_destination_id, func.count(func.distinct(TripDestination.trip_id))
        )
        .join(Trip, Trip.id == TripDestination.trip_id)
        .filter(Trip.start_date <= today)
        .group_by(TripDestination.tcc_destination_id)
        .all()
    )
    tcc_trip_counts = {tcc_id: count for tcc_id, count in tcc_trip_counts_query}

    # Get trip counts per UN country
    un_trip_counts_query = (
        db.query(TCCDestination.un_country_id, func.count(func.distinct(TripDestination.trip_id)))
        .join(TripDestination, TripDestination.tcc_destination_id == TCCDestination.id)
        .join(Trip, Trip.id == TripDestination.trip_id)
        .filter(TCCDestination.un_country_id.isnot(None))
        .filter(Trip.start_date <= today)
        .group_by(TCCDestination.un_country_id)
        .all()
    )
    un_trip_counts = {un_id: count for un_id, count in un_trip_counts_query}

    # Get visited UN countries with first_visit_date (for map coloring)
    visited_un_data = (
        db.query(UNCountry, func.min(Visit.first_visit_date).label("first_visit"))
        .join(TCCDestination, TCCDestination.un_country_id == UNCountry.id)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(Visit.first_visit_date <= today)
        .group_by(UNCountry.id)
        .all()
    )

    for country, first_visit in visited_un_data:
        visited_countries.append(country.name)
        trip_count = un_trip_counts.get(country.id, 0)
        for code in country.map_region_codes.split(","):
            code = code.strip()
            if code and first_visit:
                if code not in visited_map_regions or first_visit < visited_map_regions[code]:
                    visited_map_regions[code] = first_visit
                # Accumulate trip counts for regions with multiple polygons
                visit_counts[code] = visit_counts.get(code, 0) + trip_count

    # Get map regions from TCC destinations with their own polygon (Kosovo, Somaliland, etc.)
    visited_tcc_with_polygon = (
        db.query(TCCDestination, Visit.first_visit_date)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(
            TCCDestination.map_region_code.isnot(None),
            TCCDestination.un_country_id.is_(None),
            Visit.first_visit_date <= today,
        )
        .all()
    )

    for dest, first_visit in visited_tcc_with_polygon:
        if dest.map_region_code and first_visit:
            code = dest.map_region_code
            if code not in visited_map_regions or first_visit < visited_map_regions[code]:
                visited_map_regions[code] = first_visit
            visit_counts[code] = tcc_trip_counts.get(dest.id, 0)
            visited_countries.append(dest.name)

    # Get all microstates
    microstates = db.query(Microstate).all()
    microstates_data = [
        MicrostateData(
            name=m.name,
            longitude=m.longitude,
            latitude=m.latitude,
            map_region_code=m.map_region_code,
        )
        for m in microstates
    ]

    # Convert dates to ISO strings
    visited_map_regions_iso = {code: d.isoformat() for code, d in visited_map_regions.items()}

    # Build region names - use parent country name for all territories
    region_names: dict[str, str] = {}

    # Map all region codes to their UN country name
    all_un_countries = db.query(UNCountry).all()
    for country in all_un_countries:
        codes = [c.strip() for c in country.map_region_codes.split(",")]
        for code in codes:
            region_names[code] = country.name

    # Add names for non-UN territories with their own polygons
    tcc_with_polygon = (
        db.query(TCCDestination)
        .filter(
            TCCDestination.map_region_code.isnot(None),
            TCCDestination.un_country_id.is_(None),
        )
        .all()
    )
    for dest in tcc_with_polygon:
        if dest.map_region_code:
            region_names[dest.map_region_code] = dest.name

    return MapData(
        stats=TravelStats(
            un_visited=un_visited,
            un_total=un_total,
            un_planned=un_planned,
            tcc_visited=tcc_visited,
            tcc_total=tcc_total,
            tcc_planned=tcc_planned,
            nm_visited=nm_visited,
            nm_total=nm_total,
        ),
        visited_map_regions=visited_map_regions_iso,
        visit_counts=visit_counts,
        region_names=region_names,
        visited_countries=sorted(visited_countries),
        microstates=microstates_data,
    )


@router.get("/un-countries", response_model=UNCountriesResponse)
def get_un_countries(db: Session = Depends(get_db)) -> UNCountriesResponse:
    """Get all 193 UN countries with visit dates and counts."""

    today = date.today()

    # Get visited UN countries with last visit date (from visits table)
    visited_un_data = (
        db.query(UNCountry, func.max(Visit.first_visit_date).label("last_visit"))
        .join(TCCDestination, TCCDestination.un_country_id == UNCountry.id)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(Visit.first_visit_date <= today)
        .group_by(UNCountry.id)
        .all()
    )

    un_visit_dates: dict[int, date] = {}
    for country, last_visit in visited_un_data:
        un_visit_dates[country.id] = last_visit

    # Get trip counts per UN country (trips that have started)
    un_trip_counts = (
        db.query(TCCDestination.un_country_id, func.count(func.distinct(TripDestination.trip_id)))
        .join(TripDestination, TripDestination.tcc_destination_id == TCCDestination.id)
        .join(Trip, Trip.id == TripDestination.trip_id)
        .filter(TCCDestination.un_country_id.isnot(None))
        .filter(Trip.start_date <= today)
        .group_by(TCCDestination.un_country_id)
        .all()
    )
    un_counts: dict[int, int] = {un_id: count for un_id, count in un_trip_counts}

    # Get planned counts per UN country (first_visit_date > today)
    un_planned_counts = (
        db.query(TCCDestination.un_country_id, func.count(func.distinct(Visit.id)))
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(TCCDestination.un_country_id.isnot(None))
        .filter(Visit.first_visit_date > today)
        .group_by(TCCDestination.un_country_id)
        .all()
    )
    un_planned: dict[int, int] = {un_id: count for un_id, count in un_planned_counts}

    # Get all UN countries
    all_un_countries = db.query(UNCountry).order_by(UNCountry.continent, UNCountry.name).all()

    countries_data = [
        UNCountryData(
            name=c.name,
            continent=c.continent,
            visit_date=un_visit_dates[c.id].isoformat() if c.id in un_visit_dates else None,
            visit_count=un_counts.get(c.id, 0),
            planned_count=un_planned.get(c.id, 0),
            driving_type=c.driving_type,
            drone_flown=c.drone_flown,
        )
        for c in all_un_countries
    ]

    return UNCountriesResponse(countries=countries_data)


@router.patch("/un-countries/{country_name}/activities")
def update_un_country_activities(
    country_name: str,
    update: UNCountryActivityUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> UNCountryData:
    """Update driving and drone activities for a UN country (admin only)."""
    country = db.query(UNCountry).filter(UNCountry.name == country_name).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    # Update the fields
    country.driving_type = update.driving_type
    country.drone_flown = update.drone_flown
    db.commit()
    db.refresh(country)

    # Get visit info for response
    today = date.today()

    last_visit = (
        db.query(func.max(Visit.first_visit_date))
        .join(TCCDestination, TCCDestination.id == Visit.tcc_destination_id)
        .filter(TCCDestination.un_country_id == country.id)
        .filter(Visit.first_visit_date <= today)
        .scalar()
    )

    visit_count = (
        db.query(func.count(func.distinct(TripDestination.trip_id)))
        .join(TCCDestination, TripDestination.tcc_destination_id == TCCDestination.id)
        .join(Trip, Trip.id == TripDestination.trip_id)
        .filter(TCCDestination.un_country_id == country.id)
        .filter(Trip.start_date <= today)
        .scalar()
        or 0
    )

    return UNCountryData(
        name=country.name,
        continent=country.continent,
        visit_date=last_visit.isoformat() if last_visit else None,
        visit_count=visit_count,
        planned_count=0,
        driving_type=country.driving_type,
        drone_flown=country.drone_flown,
    )


@router.get("/tcc-destinations", response_model=TCCDestinationsResponse)
def get_tcc_destinations(db: Session = Depends(get_db)) -> TCCDestinationsResponse:
    """Get all 330 TCC destinations with visit dates and counts."""

    today = date.today()

    # Get visit dates per TCC destination (from visits table, where visited)
    tcc_visit_data = (
        db.query(
            Visit.tcc_destination_id,
            Visit.first_visit_date,
        )
        .filter(Visit.first_visit_date <= today)
        .all()
    )
    tcc_visit_dates: dict[int, date] = {tcc_id: visit_date for tcc_id, visit_date in tcc_visit_data}

    # Get trip counts per TCC destination (trips that have started)
    tcc_trip_counts = (
        db.query(
            TripDestination.tcc_destination_id,
            func.count(func.distinct(TripDestination.trip_id)).label("trip_count"),
        )
        .join(Trip, Trip.id == TripDestination.trip_id)
        .filter(Trip.start_date <= today)
        .group_by(TripDestination.tcc_destination_id)
        .all()
    )
    tcc_counts: dict[int, int] = {tcc_id: count for tcc_id, count in tcc_trip_counts}

    # Get planned counts per TCC destination (first_visit_date > today)
    tcc_planned_data = (
        db.query(Visit.tcc_destination_id).filter(Visit.first_visit_date > today).all()
    )
    tcc_planned: dict[int, int] = {tcc_id: 1 for (tcc_id,) in tcc_planned_data}

    all_tcc = (
        db.query(TCCDestination).order_by(TCCDestination.tcc_region, TCCDestination.name).all()
    )

    destinations_data = [
        TCCDestinationData(
            name=dest.name,
            region=dest.tcc_region,
            visit_date=tcc_visit_dates[dest.id].isoformat() if dest.id in tcc_visit_dates else None,
            visit_count=tcc_counts.get(dest.id, 0),
            planned_count=tcc_planned.get(dest.id, 0),
        )
        for dest in all_tcc
    ]

    return TCCDestinationsResponse(destinations=destinations_data)


@router.get("/map-cities", response_model=MapCitiesResponse)
def get_map_cities(db: Session = Depends(get_db)) -> MapCitiesResponse:
    """Get all properly visited cities with coordinates for map markers."""

    today = date.today()

    # Get distinct cities from visited destinations (first_visit_date <= today)
    # Only include cities where their country_code matches a TCC destination
    # on the SAME trip (filters out cities with wrong country codes)
    # For territories (Jersey, Guernsey, etc.) use TCCDestination.iso_alpha2
    # which has the correct territory code; fall back to UNCountry.iso_alpha2
    # Use MIN(is_partial) so if a city has both partial and full visits, show as full
    cities = (
        db.query(
            City.name,
            City.lat,
            City.lng,
            func.min(TripCity.is_partial).label("is_partial"),
        )
        .join(TripCity, TripCity.city_id == City.id)
        .join(Trip, Trip.id == TripCity.trip_id)
        .join(TripDestination, TripDestination.trip_id == Trip.id)
        .join(TCCDestination, TCCDestination.id == TripDestination.tcc_destination_id)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .outerjoin(UNCountry, UNCountry.id == TCCDestination.un_country_id)
        .filter(City.lat.isnot(None))
        .filter(City.lng.isnot(None))
        .filter(
            func.lower(City.country_code)
            == func.lower(coalesce(TCCDestination.iso_alpha2, UNCountry.iso_alpha2))
        )
        .filter(Visit.first_visit_date <= today)
        .group_by(City.name, City.lat, City.lng)
        .all()
    )

    return MapCitiesResponse(
        cities=[
            CityMarkerData(name=name, lat=lat, lng=lng, is_partial=bool(is_partial))
            for name, lat, lng, is_partial in cities
        ]
    )


@router.get("/map-flights", response_model=FlightMapData)
def get_map_flights(db: Session = Depends(get_db)) -> FlightMapData:
    """Get airports and flight routes for the map flights layer (past flights only)."""
    today = date.today()

    # Only include past/today flights
    past_flights = (
        db.query(Flight.departure_airport_id, Flight.arrival_airport_id)
        .filter(Flight.flight_date <= today)
        .all()
    )

    # Get unique airport IDs from past flights only
    dep_ids = {r[0] for r in past_flights}
    arr_ids = {r[1] for r in past_flights}
    all_ids = dep_ids | arr_ids

    airports = (
        db.query(Airport)
        .filter(Airport.id.in_(all_ids))
        .filter(Airport.latitude.isnot(None), Airport.longitude.isnot(None))
        .all()
    )

    airport_data = [
        FlightMapAirport(
            iata_code=a.iata_code,
            name=a.name,
            lat=a.latitude,  # type: ignore[arg-type]  # filtered above
            lng=a.longitude,  # type: ignore[arg-type]  # filtered above
        )
        for a in airports
    ]

    # Get route counts (normalize direction: always smaller IATA first)
    flights = past_flights

    # Build IATA lookup
    iata_by_id = {a.id: a.iata_code for a in airports}
    route_counts: dict[tuple[str, str], int] = {}
    for dep_id, arr_id in flights:
        dep_iata = iata_by_id.get(dep_id)
        arr_iata = iata_by_id.get(arr_id)
        if not dep_iata or not arr_iata:
            continue
        # Normalize: alphabetically smaller first
        key = (min(dep_iata, arr_iata), max(dep_iata, arr_iata))
        route_counts[key] = route_counts.get(key, 0) + 1

    route_data = [
        FlightMapRoute(from_iata=k[0], to_iata=k[1], count=v) for k, v in route_counts.items()
    ]

    # Count airports per country code
    cc_counts: dict[str, int] = {}
    for a in airports:
        if a.country_code:
            cc_counts[a.country_code] = cc_counts.get(a.country_code, 0) + 1

    # Map country codes to region codes with airport counts
    country_regions: dict[str, int] = {}
    if cc_counts:
        un_countries = (
            db.query(UNCountry.iso_alpha2, UNCountry.map_region_codes)
            .filter(UNCountry.iso_alpha2.in_(cc_counts.keys()))
            .all()
        )
        for iso2, codes_str in un_countries:
            count = cc_counts[iso2]
            for code in codes_str.split(","):
                country_regions[code.strip()] = count

    return FlightMapData(
        airports=airport_data,
        routes=route_data,
        country_regions=country_regions,
    )
