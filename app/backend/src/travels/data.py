from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Microstate, NMRegion, TCCDestination, TripDestination, UNCountry, Visit
from .models import (
    MapData,
    MicrostateData,
    NMRegionData,
    TCCDestinationData,
    TCCDestinationsResponse,
    TravelData,
    TravelStats,
    UNCountriesResponse,
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

    # Get NM stats
    nm_total = db.query(func.count(NMRegion.id)).scalar() or 0
    nm_visited = db.query(func.count(NMRegion.id)).filter(NMRegion.visited.is_(True)).scalar() or 0

    # Get all map region codes with their first visit dates and trip counts
    visited_map_regions: dict[str, date] = {}
    visit_counts: dict[str, int] = {}
    visited_countries: list[str] = []

    # Count trips per TCC destination (distinct trips in case of duplicates)
    trip_counts_query = (
        db.query(
            TripDestination.tcc_destination_id, func.count(func.distinct(TripDestination.trip_id))
        )
        .group_by(TripDestination.tcc_destination_id)
        .all()
    )
    tcc_trip_counts = {tcc_id: count for tcc_id, count in trip_counts_query}

    # Get trip counts per UN country (count distinct trips, not trip_destinations)
    un_trip_counts_query = (
        db.query(TCCDestination.un_country_id, func.count(func.distinct(TripDestination.trip_id)))
        .join(TripDestination, TripDestination.tcc_destination_id == TCCDestination.id)
        .filter(TCCDestination.un_country_id.isnot(None))
        .group_by(TCCDestination.un_country_id)
        .all()
    )
    un_trip_counts = {un_id: count for un_id, count in un_trip_counts_query}

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
        trip_count = un_trip_counts.get(country.id, 0)
        for code in country.map_region_codes.split(","):
            code = code.strip()
            if code and first_visit:
                if code not in visited_map_regions or first_visit < visited_map_regions[code]:
                    visited_map_regions[code] = first_visit
                # Accumulate trip counts for regions with multiple polygons
                visit_counts[code] = visit_counts.get(code, 0) + trip_count

    # Get map regions from TCC destinations with their own polygon
    visited_tcc_with_polygon = (
        db.query(TCCDestination, Visit.first_visit_date)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(
            TCCDestination.map_region_code.isnot(None),
            TCCDestination.un_country_id.is_(None),
            Visit.first_visit_date.isnot(None),
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

    return MapData(
        stats=TravelStats(
            un_visited=un_visited,
            un_total=un_total,
            tcc_visited=tcc_visited,
            tcc_total=tcc_total,
            nm_visited=nm_visited,
            nm_total=nm_total,
        ),
        visited_map_regions=visited_map_regions_iso,
        visit_counts=visit_counts,
        visited_countries=sorted(visited_countries),
        microstates=microstates_data,
    )


@router.get("/un-countries", response_model=UNCountriesResponse)
def get_un_countries(db: Session = Depends(get_db)) -> UNCountriesResponse:
    """Get all 193 UN countries with visit dates."""

    # Get visited UN countries with earliest visit date
    visited_un_data = (
        db.query(UNCountry, func.min(Visit.first_visit_date).label("first_visit"))
        .join(TCCDestination, TCCDestination.un_country_id == UNCountry.id)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(Visit.first_visit_date.isnot(None))
        .group_by(UNCountry.id)
        .all()
    )

    un_visit_dates: dict[int, date] = {}
    for country, first_visit in visited_un_data:
        un_visit_dates[country.id] = first_visit

    # Get all UN countries
    all_un_countries = db.query(UNCountry).order_by(UNCountry.continent, UNCountry.name).all()

    countries_data = [
        UNCountryData(
            name=c.name,
            continent=c.continent,
            visit_date=un_visit_dates[c.id].isoformat() if c.id in un_visit_dates else None,
        )
        for c in all_un_countries
    ]

    return UNCountriesResponse(countries=countries_data)


@router.get("/tcc-destinations", response_model=TCCDestinationsResponse)
def get_tcc_destinations(db: Session = Depends(get_db)) -> TCCDestinationsResponse:
    """Get all 330 TCC destinations with visit dates."""

    all_tcc = (
        db.query(TCCDestination, Visit.first_visit_date)
        .outerjoin(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .order_by(TCCDestination.tcc_region, TCCDestination.name)
        .all()
    )

    destinations_data = [
        TCCDestinationData(
            name=dest.name,
            region=dest.tcc_region,
            visit_date=visit_date.isoformat() if visit_date else None,
        )
        for dest, visit_date in all_tcc
    ]

    return TCCDestinationsResponse(destinations=destinations_data)
