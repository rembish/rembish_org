"""Drone and drone flight CRUD + public stats."""

from collections import defaultdict
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth.session import get_admin_user, get_trips_viewer
from ..database import get_db
from ..models import Drone, DroneFlight, Trip, User
from .models import (
    DroneCreateRequest,
    DroneData,
    DroneFlightCreateRequest,
    DroneFlightData,
    DroneFlightMapPoint,
    DroneFlightsResponse,
    DroneFlightYearStats,
    DronesResponse,
    DroneStatsPerDrone,
    DroneStatsResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _drone_to_data(drone: Drone, flights_count: int) -> DroneData:
    return DroneData(
        id=drone.id,
        name=drone.name,
        model=drone.model,
        serial_number=drone.serial_number,
        acquired_date=drone.acquired_date.isoformat() if drone.acquired_date else None,
        retired_date=drone.retired_date.isoformat() if drone.retired_date else None,
        notes=drone.notes,
        flights_count=flights_count,
    )


def _flight_to_data(f: DroneFlight) -> DroneFlightData:
    return DroneFlightData(
        id=f.id,
        drone_id=f.drone_id,
        trip_id=f.trip_id,
        flight_date=f.flight_date.isoformat(),
        takeoff_time=f.takeoff_time.isoformat() if f.takeoff_time else None,
        latitude=f.latitude,
        longitude=f.longitude,
        duration_sec=f.duration_sec,
        distance_km=f.distance_km,
        max_speed_ms=f.max_speed_ms,
        photos=f.photos,
        video_sec=f.video_sec,
        country=f.country,
        city=f.city,
        is_hidden=f.is_hidden,
        source_file=f.source_file,
        drone_name=f.drone.name if f.drone else None,
        drone_model=f.drone.model if f.drone else None,
    )


# ---------------------------------------------------------------------------
# Drones CRUD (admin only)
# ---------------------------------------------------------------------------


@router.get("/drones", response_model=DronesResponse)
def list_drones(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> DronesResponse:
    """List all drones with flight counts."""
    drones = db.query(Drone).order_by(Drone.name).all()
    counts: dict[int, int] = {}
    for drone_id, cnt in (
        db.query(DroneFlight.drone_id, func.count(DroneFlight.id))
        .filter(DroneFlight.drone_id.isnot(None))
        .group_by(DroneFlight.drone_id)
        .all()
    ):
        counts[drone_id] = cnt
    return DronesResponse(drones=[_drone_to_data(d, counts.get(d.id, 0)) for d in drones])


@router.post("/drones", response_model=DroneData)
def create_drone(
    body: DroneCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> DroneData:
    """Create a new drone."""
    drone = Drone(
        name=body.name,
        model=body.model,
        serial_number=body.serial_number,
        acquired_date=date.fromisoformat(body.acquired_date) if body.acquired_date else None,
        retired_date=date.fromisoformat(body.retired_date) if body.retired_date else None,
        notes=body.notes,
    )
    db.add(drone)
    db.commit()
    db.refresh(drone)
    return _drone_to_data(drone, 0)


@router.put("/drones/{drone_id}", response_model=DroneData)
def update_drone(
    drone_id: int,
    body: DroneCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> DroneData:
    """Update a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    drone.name = body.name
    drone.model = body.model
    drone.serial_number = body.serial_number
    drone.acquired_date = date.fromisoformat(body.acquired_date) if body.acquired_date else None
    drone.retired_date = date.fromisoformat(body.retired_date) if body.retired_date else None
    drone.notes = body.notes
    db.commit()
    db.refresh(drone)
    cnt = db.query(DroneFlight).filter(DroneFlight.drone_id == drone_id).count()
    return _drone_to_data(drone, cnt)


@router.delete("/drones/{drone_id}", status_code=204)
def delete_drone(
    drone_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a drone (sets flights' drone_id to NULL)."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    # Detach flights from this drone
    db.query(DroneFlight).filter(DroneFlight.drone_id == drone_id).update(
        {DroneFlight.drone_id: None}
    )
    db.delete(drone)
    db.commit()


# ---------------------------------------------------------------------------
# Drone Flights CRUD
# ---------------------------------------------------------------------------


@router.get("/drone-flights", response_model=DroneFlightsResponse)
def list_drone_flights(
    viewer: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
    drone_id: int | None = Query(None),
    year: int | None = Query(None),
    country: str | None = Query(None),
    trip_id: int | None = Query(None),
) -> DroneFlightsResponse:
    """List drone flights with optional filters. Viewers see non-hidden only."""
    q = db.query(DroneFlight)
    is_admin = viewer.role == "admin"
    if not is_admin:
        q = q.filter(DroneFlight.is_hidden == False)  # noqa: E712
    if drone_id is not None:
        q = q.filter(DroneFlight.drone_id == drone_id)
    if year is not None:
        q = q.filter(
            DroneFlight.flight_date >= date(year, 1, 1),
            DroneFlight.flight_date <= date(year, 12, 31),
        )
    if country is not None:
        q = q.filter(DroneFlight.country == country.upper())
    if trip_id is not None:
        q = q.filter(DroneFlight.trip_id == trip_id)
    total = q.count()
    flights = q.order_by(DroneFlight.flight_date.desc(), DroneFlight.takeoff_time.desc()).all()
    return DroneFlightsResponse(
        flights=[_flight_to_data(f) for f in flights],
        total=total,
    )


@router.post("/drone-flights", response_model=DroneFlightData)
def create_drone_flight(
    body: DroneFlightCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> DroneFlightData:
    """Create a drone flight."""
    f = DroneFlight(
        drone_id=body.drone_id,
        trip_id=body.trip_id,
        flight_date=date.fromisoformat(body.flight_date),
        takeoff_time=(datetime.fromisoformat(body.takeoff_time) if body.takeoff_time else None),
        latitude=body.latitude,
        longitude=body.longitude,
        duration_sec=body.duration_sec,
        distance_km=body.distance_km,
        max_speed_ms=body.max_speed_ms,
        photos=body.photos,
        video_sec=body.video_sec,
        country=body.country,
        city=body.city,
        is_hidden=body.is_hidden,
        source_file=body.source_file,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return _flight_to_data(f)


@router.put("/drone-flights/{flight_id}", response_model=DroneFlightData)
def update_drone_flight(
    flight_id: int,
    body: DroneFlightCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> DroneFlightData:
    """Update a drone flight."""
    f = db.query(DroneFlight).filter(DroneFlight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Drone flight not found")
    f.drone_id = body.drone_id
    f.trip_id = body.trip_id
    f.flight_date = date.fromisoformat(body.flight_date)
    f.takeoff_time = datetime.fromisoformat(body.takeoff_time) if body.takeoff_time else None
    f.latitude = body.latitude
    f.longitude = body.longitude
    f.duration_sec = body.duration_sec
    f.distance_km = body.distance_km
    f.max_speed_ms = body.max_speed_ms
    f.photos = body.photos
    f.video_sec = body.video_sec
    f.country = body.country
    f.city = body.city
    f.is_hidden = body.is_hidden
    f.source_file = body.source_file
    db.commit()
    db.refresh(f)
    return _flight_to_data(f)


@router.delete("/drone-flights/{flight_id}", status_code=204)
def delete_drone_flight(
    flight_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a drone flight."""
    f = db.query(DroneFlight).filter(DroneFlight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Drone flight not found")
    db.delete(f)
    db.commit()


@router.put("/drone-flights/{flight_id}/hide", response_model=DroneFlightData)
def toggle_hide_drone_flight(
    flight_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> DroneFlightData:
    """Toggle is_hidden flag on a drone flight."""
    f = db.query(DroneFlight).filter(DroneFlight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Drone flight not found")
    f.is_hidden = not f.is_hidden
    db.commit()
    db.refresh(f)
    return _flight_to_data(f)


@router.put("/drone-flights/{flight_id}/trip", response_model=DroneFlightData)
def assign_trip_to_drone_flight(
    flight_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    trip_id: int | None = Query(None),
) -> DroneFlightData:
    """Assign or unassign a trip to a drone flight."""
    f = db.query(DroneFlight).filter(DroneFlight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Drone flight not found")
    if trip_id is not None:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
    f.trip_id = trip_id
    db.commit()
    db.refresh(f)
    return _flight_to_data(f)


# ---------------------------------------------------------------------------
# Trip-scoped drone flights (read-only)
# ---------------------------------------------------------------------------


@router.get("/trips/{trip_id}/drone-flights", response_model=DroneFlightsResponse)
def get_trip_drone_flights(
    trip_id: int,
    viewer: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> DroneFlightsResponse:
    """Get drone flights for a specific trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    q = db.query(DroneFlight).filter(DroneFlight.trip_id == trip_id)
    if viewer.role != "admin":
        q = q.filter(DroneFlight.is_hidden == False)  # noqa: E712
    flights = q.order_by(DroneFlight.flight_date, DroneFlight.takeoff_time).all()
    return DroneFlightsResponse(flights=[_flight_to_data(f) for f in flights], total=len(flights))


# ---------------------------------------------------------------------------
# Stats (public — no auth required)
# ---------------------------------------------------------------------------


@router.get("/drone-stats", response_model=DroneStatsResponse)
def get_drone_stats(
    db: Session = Depends(get_db),
) -> DroneStatsResponse:
    """Public drone flight statistics (excludes hidden flights)."""
    visible = db.query(DroneFlight).filter(DroneFlight.is_hidden == False)  # noqa: E712

    flights = visible.all()
    if not flights:
        return DroneStatsResponse(
            total_flights=0,
            total_distance_km=0.0,
            total_duration_sec=0.0,
            total_countries=0,
            total_photos=0,
            total_video_sec=0,
            first_flight_date=None,
            last_flight_date=None,
            by_year=[],
            by_drone=[],
        )

    total_distance = sum(f.distance_km or 0.0 for f in flights)
    total_duration = sum(f.duration_sec or 0.0 for f in flights)
    total_photos = sum(f.photos for f in flights)
    total_video = sum(f.video_sec for f in flights)
    countries = {f.country for f in flights if f.country}
    dates = [f.flight_date for f in flights]

    # by_year
    year_counts: dict[int, int] = defaultdict(int)
    year_distance: dict[int, float] = defaultdict(float)
    year_duration: dict[int, float] = defaultdict(float)
    year_countries: dict[int, set[str]] = defaultdict(set)
    for f in flights:
        y = f.flight_date.year
        year_counts[y] += 1
        year_distance[y] += f.distance_km or 0.0
        year_duration[y] += f.duration_sec or 0.0
        if f.country:
            year_countries[y].add(f.country)

    by_year = [
        DroneFlightYearStats(
            year=y,
            flights_count=year_counts[y],
            total_distance_km=round(year_distance[y], 2),
            total_duration_sec=round(year_duration[y], 1),
            countries=sorted(year_countries[y]),
        )
        for y in sorted(year_counts)
    ]

    # by_drone
    drone_counts: dict[int, int] = defaultdict(int)
    drone_distance: dict[int, float] = defaultdict(float)
    drone_duration: dict[int, float] = defaultdict(float)
    drone_names: dict[int, str] = {}
    drone_models: dict[int, str] = {}
    for f in flights:
        if f.drone_id is None:
            continue
        drone_counts[f.drone_id] += 1
        drone_distance[f.drone_id] += f.distance_km or 0.0
        drone_duration[f.drone_id] += f.duration_sec or 0.0
        if f.drone_id not in drone_names:
            drone_names[f.drone_id] = f.drone.name if f.drone else "Unknown"
            drone_models[f.drone_id] = f.drone.model if f.drone else "Unknown"

    by_drone = [
        DroneStatsPerDrone(
            drone_id=did,
            drone_name=drone_names[did],
            drone_model=drone_models[did],
            flights_count=drone_counts[did],
            total_distance_km=round(drone_distance[did], 2),
            total_duration_sec=round(drone_duration[did], 1),
        )
        for did in sorted(drone_counts)
    ]

    return DroneStatsResponse(
        total_flights=len(flights),
        total_distance_km=round(total_distance, 2),
        total_duration_sec=round(total_duration, 1),
        total_countries=len(countries),
        total_photos=total_photos,
        total_video_sec=total_video,
        first_flight_date=min(dates).isoformat(),
        last_flight_date=max(dates).isoformat(),
        by_year=by_year,
        by_drone=by_drone,
    )


# ---------------------------------------------------------------------------
# Map data (viewer only)
# ---------------------------------------------------------------------------


@router.get("/drone-flights/map", response_model=list[DroneFlightMapPoint])
def get_drone_flights_map(
    viewer: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> list[DroneFlightMapPoint]:
    """Return map points for non-hidden flights with valid coordinates."""
    is_admin = viewer.role == "admin"
    q = db.query(DroneFlight).filter(
        DroneFlight.latitude.isnot(None),
        DroneFlight.longitude.isnot(None),
    )
    if not is_admin:
        q = q.filter(DroneFlight.is_hidden == False)  # noqa: E712
    flights = q.all()
    return [
        DroneFlightMapPoint(
            lat=f.latitude,  # type: ignore[arg-type]
            lng=f.longitude,  # type: ignore[arg-type]
            drone_model=f.drone.model if f.drone else None,
            country=f.country,
            date=f.flight_date.isoformat(),
            flight_path=f.flight_path,
        )
        for f in flights
    ]
