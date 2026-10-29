"""GPS logger tracks: raw CSV upload to a trip, automatic legs, admin-only viewing.

Raw CSVs are the most sensitive data the site holds (exact positions to the second),
so they live in private vault storage and every endpoint here is admin-only.
"""

import gzip
from datetime import UTC, datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user
from ..database import get_db
from ..log_config import get_logger
from ..models import GpsTrack, GpsTrackLeg, TCCDestination, Trip, TripDestination, User
from ..vault_storage import get_vault_storage
from .gps_processing import (
    PROCESSING_VERSION,
    Leg,
    ProcessedTrack,
    Window,
    legs_from_windows,
    parse_csv,
    parse_time,
    process_points,
    validate_windows,
)

log = get_logger(__name__)

router = APIRouter()

MAX_CSV_SIZE = 10 * 1024 * 1024  # a full 1 Hz day is about 1.6 MB


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class GpsLegData(BaseModel):
    id: int
    seq: int
    mode: str
    started_at: str
    ended_at: str
    distance_km: float
    max_speed_kmh: float
    lat: float
    lon: float
    lines: list[list[list[float]]]
    title: str | None
    note: str | None
    is_hidden: bool


class GpsTrackData(BaseModel):
    id: int
    source_file: str
    local_date: str
    timezone: str
    started_at: str
    ended_at: str
    point_count: int
    wake_count: int
    poi_count: int
    distance_km: float
    max_speed_kmh: float
    title: str | None
    note: str | None
    legs_source: str
    processing_version: int
    legs: list[GpsLegData]


class GpsTracksResponse(BaseModel):
    tracks: list[GpsTrackData]
    default_timezone: str


class GpsUploadResult(BaseModel):
    file: str
    status: str  # created | replaced | error
    detail: str | None = None
    track_id: int | None = None


class GpsUploadResponse(BaseModel):
    results: list[GpsUploadResult]


class GpsReprocessRequest(BaseModel):
    timezone: str | None = None
    # Reprocessing an analysed day replaces its analysis; this makes that explicit.
    discard_analysis: bool = False


class AnalysisLegIn(BaseModel):
    start: str  # ISO-8601 with offset
    end: str
    mode: str
    title: str | None = None
    note: str | None = None
    hidden: bool = False


class AnalysisDayIn(BaseModel):
    source_file: str
    started_at: str | None = None  # only needed if two days share a file name
    title: str | None = None
    note: str | None = None
    legs: list[AnalysisLegIn]


class AnalysisUpload(BaseModel):
    format: Literal["rembish-gps-analysis/1"]
    days: list[AnalysisDayIn]


class AnalysisDayResult(BaseModel):
    source_file: str
    track_id: int
    legs: int


class AnalysisResponse(BaseModel):
    days: list[AnalysisDayResult]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_iso(dt: datetime) -> str:
    """DB datetimes are naive UTC; make that explicit for the browser."""
    return dt.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


def _naive_utc(dt: datetime) -> datetime:
    return dt.astimezone(UTC).replace(tzinfo=None)


def _track_to_data(track: GpsTrack) -> GpsTrackData:
    return GpsTrackData(
        id=track.id,
        source_file=track.source_file,
        local_date=track.local_date.isoformat(),
        timezone=track.timezone,
        started_at=_utc_iso(track.started_at),
        ended_at=_utc_iso(track.ended_at),
        point_count=track.point_count,
        wake_count=track.wake_count,
        poi_count=track.poi_count,
        distance_km=track.distance_km,
        max_speed_kmh=track.max_speed_kmh,
        title=track.title,
        note=track.note,
        legs_source=track.legs_source,
        processing_version=track.processing_version,
        legs=[
            GpsLegData(
                id=leg.id,
                seq=leg.seq,
                mode=leg.mode,
                started_at=_utc_iso(leg.started_at),
                ended_at=_utc_iso(leg.ended_at),
                distance_km=leg.distance_km,
                max_speed_kmh=leg.max_speed_kmh,
                lat=leg.lat,
                lon=leg.lon,
                lines=leg.lines,
                title=leg.title,
                note=leg.note,
                is_hidden=leg.is_hidden,
            )
            for leg in track.legs
        ],
    )


def _default_timezone(trip: Trip) -> str:
    """Time zone of the trip's first destination that has one; UTC otherwise."""
    for td in trip.destinations:
        tz = td.tcc_destination.timezone or (
            td.tcc_destination.un_country.timezone if td.tcc_destination.un_country else None
        )
        if tz:
            return tz
    return "UTC"


def _validate_timezone(tz: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(status_code=400, detail=f"Unknown time zone: {tz}")


def _get_trip(db: Session, trip_id: int) -> Trip:
    trip = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations)
            .joinedload(TripDestination.tcc_destination)
            .joinedload(TCCDestination.un_country)
        )
        .filter(Trip.id == trip_id)
        .first()
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


def _get_track(db: Session, track_id: int) -> GpsTrack:
    track = db.query(GpsTrack).filter(GpsTrack.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


def _apply(db: Session, track: GpsTrack, processed: ProcessedTrack, tz: ZoneInfo) -> None:
    """Write processing results onto a track, replacing its legs."""
    track.started_at = _naive_utc(processed.started_at)
    track.ended_at = _naive_utc(processed.ended_at)
    track.timezone = str(tz)
    track.local_date = processed.started_at.astimezone(tz).date()
    track.point_count = processed.point_count
    track.wake_count = processed.wake_count
    track.poi_count = processed.poi_count
    track.distance_km = processed.distance_km
    track.max_speed_kmh = processed.max_speed_kmh
    track.legs_source = "auto"
    track.processing_version = PROCESSING_VERSION

    track.title = None
    track.note = None
    _replace_legs(db, track, processed.legs)


def _replace_legs(db: Session, track: GpsTrack, legs: list[Leg]) -> None:
    # Flush the deletes first: (track_id, seq) is unique.
    track.legs.clear()
    db.flush()
    for seq, leg in enumerate(legs):
        track.legs.append(
            GpsTrackLeg(
                seq=seq,
                mode=leg.mode,
                started_at=_naive_utc(leg.started_at),
                ended_at=_naive_utc(leg.ended_at),
                distance_km=leg.distance_km,
                max_speed_kmh=leg.max_speed_kmh,
                lat=leg.lat,
                lon=leg.lon,
                lines=leg.lines,
                title=leg.title,
                note=leg.note,
                is_hidden=leg.is_hidden,
            )
        )


def _read_raw(track: GpsTrack) -> bytes:
    try:
        stored = get_vault_storage().read(track.raw_path)
    except Exception:
        log.error("Vault storage read failed for GPS track %s", track.id, exc_info=True)
        raise HTTPException(status_code=502, detail="Could not read raw track from storage")
    if stored is None:
        raise HTTPException(status_code=404, detail="Raw track file not found in storage")
    return gzip.decompress(stored)


def _delete_raw(key: str) -> None:
    try:
        get_vault_storage().delete(key)
    except Exception:
        log.warning("Vault storage delete failed for GPS raw file %s", key, exc_info=True)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/trips/{trip_id}/gps-tracks", response_model=GpsTracksResponse)
def list_trip_gps_tracks(
    trip_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> GpsTracksResponse:
    """All track days of a trip with their legs, oldest first."""
    trip = _get_trip(db, trip_id)
    tracks = (
        db.query(GpsTrack)
        .options(joinedload(GpsTrack.legs))
        .filter(GpsTrack.trip_id == trip_id)
        .order_by(GpsTrack.started_at)
        .all()
    )
    return GpsTracksResponse(
        tracks=[_track_to_data(t) for t in tracks],
        default_timezone=_default_timezone(trip),
    )


@router.post("/trips/{trip_id}/gps-tracks/upload", response_model=GpsUploadResponse)
async def upload_trip_gps_tracks(
    trip_id: int,
    files: Annotated[list[UploadFile], File()],
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    timezone: Annotated[str | None, Form()] = None,
) -> GpsUploadResponse:
    """Upload logger day CSVs. Re-uploading the same day replaces it."""
    trip = _get_trip(db, trip_id)
    tz = _validate_timezone(timezone or _default_timezone(trip))
    storage = get_vault_storage()
    results: list[GpsUploadResult] = []

    for file in files:
        name = file.filename or "track.csv"

        def fail(detail: str, name: str = name) -> None:
            results.append(GpsUploadResult(file=name, status="error", detail=detail))

        if not name.lower().endswith(".csv"):
            fail("Only .csv logger files are accepted")
            continue
        content = await file.read()
        if not content:
            fail("File is empty")
            continue
        if len(content) > MAX_CSV_SIZE:
            fail("File too large (max 10 MB)")
            continue

        try:
            processed = process_points(parse_csv(content))
        except ValueError as e:
            fail(str(e))
            continue

        started = _naive_utc(processed.started_at)
        track = db.query(GpsTrack).filter(GpsTrack.started_at == started).first()
        if track and track.trip_id not in (None, trip_id):
            fail(f"This day is already uploaded to trip #{track.trip_id}")
            continue
        if track and track.legs_source == "annotated":
            fail("This day has an analysis uploaded; delete the track first to replace it")
            continue

        try:
            key = storage.save(admin.id, f"{name}.gz", gzip.compress(content), "application/gzip")
        except Exception:
            log.error("Vault storage save failed for GPS track %s", name, exc_info=True)
            fail("Could not store the raw file")
            continue

        old_key = track.raw_path if track else None
        status = "replaced" if track else "created"
        if not track:
            track = GpsTrack(raw_path=key, raw_size=len(content))
            db.add(track)
        track.trip_id = trip_id
        track.source_file = name
        track.raw_path = key
        track.raw_size = len(content)
        _apply(db, track, processed, tz)
        db.commit()
        if old_key and old_key != key:
            _delete_raw(old_key)

        log.info(
            "GPS track %s %s for trip %s: %d points, %d legs",
            name,
            status,
            trip_id,
            processed.point_count,
            len(processed.legs),
        )
        results.append(GpsUploadResult(file=name, status=status, track_id=track.id))

    return GpsUploadResponse(results=results)


@router.post("/trips/{trip_id}/gps-tracks/analysis", response_model=AnalysisResponse)
def upload_trip_gps_analysis(
    trip_id: int,
    body: AnalysisUpload,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """Replace the legs of analysed days with the given windows.

    Every day is validated first; if anything is wrong nothing is applied and the
    422 lists all problems.
    """
    _get_trip(db, trip_id)
    tracks = db.query(GpsTrack).filter(GpsTrack.trip_id == trip_id).all()
    errors: list[str] = []
    planned: list[tuple[GpsTrack, AnalysisDayIn, list[Leg]]] = []
    seen: set[int] = set()

    for day in body.days:
        label = day.source_file
        matches = [t for t in tracks if t.source_file.lower() == day.source_file.lower()]
        if day.started_at:
            try:
                started = _naive_utc(parse_time(day.started_at))
            except ValueError as e:
                errors.append(f"{label}: {e}")
                continue
            matches = [t for t in matches if t.started_at == started]
        if len(matches) != 1:
            errors.append(
                f"{label}: {'no' if not matches else 'more than one'} matching track in this trip"
            )
            continue
        track = matches[0]
        if track.id in seen:
            errors.append(f"{label}: listed twice")
            continue
        seen.add(track.id)

        try:
            windows = [
                Window(
                    start=parse_time(leg.start),
                    end=parse_time(leg.end),
                    mode=leg.mode,
                    title=(leg.title or "").strip() or None,
                    note=(leg.note or "").strip() or None,
                    hidden=leg.hidden,
                )
                for leg in day.legs
            ]
        except ValueError as e:
            errors.append(f"{label}: {e}")
            continue
        start = track.started_at.replace(tzinfo=UTC)
        end = track.ended_at.replace(tzinfo=UTC)
        problems = validate_windows(windows, start, end)
        if problems:
            errors.extend(f"{label}: {p}" for p in problems)
            continue
        try:
            points = parse_csv(_read_raw(track))
        except ValueError as e:
            errors.append(f"{label}: raw file unreadable: {e}")
            continue
        planned.append((track, day, legs_from_windows(points, windows)))

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    for track, day, legs in planned:
        _replace_legs(db, track, legs)
        track.title = (day.title or "").strip() or None
        track.note = (day.note or "").strip() or None
        track.legs_source = "annotated"
        track.distance_km = round(
            sum(leg.distance_km for leg in legs if leg.mode not in ("gap", "stop")), 3
        )
    db.commit()
    log.info("GPS analysis applied to trip %s: %d days", trip_id, len(planned))
    return AnalysisResponse(
        days=[
            AnalysisDayResult(source_file=t.source_file, track_id=t.id, legs=len(legs))
            for t, _, legs in planned
        ]
    )


@router.post("/gps-tracks/{track_id}/reprocess", response_model=GpsTrackData)
def reprocess_gps_track(
    track_id: int,
    body: GpsReprocessRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> GpsTrackData:
    """Re-run automatic processing from the stored raw file, optionally in another zone."""
    track = _get_track(db, track_id)
    if track.legs_source == "annotated" and not body.discard_analysis:
        raise HTTPException(
            status_code=409, detail="Track has an analysis uploaded; reprocessing would drop it"
        )
    tz = _validate_timezone(body.timezone or track.timezone)
    try:
        processed = process_points(parse_csv(_read_raw(track)))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    _apply(db, track, processed, tz)
    db.commit()
    db.refresh(track)
    return _track_to_data(track)


@router.get("/gps-tracks/{track_id}/raw")
def download_gps_track_raw(
    track_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> Response:
    """The original logger CSV, for local analysis."""
    track = _get_track(db, track_id)
    return Response(
        content=_read_raw(track),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{track.source_file}"'},
    )


@router.delete("/gps-tracks/{track_id}", status_code=204)
def delete_gps_track(
    track_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a track day, its legs and its raw file."""
    track = _get_track(db, track_id)
    key = track.raw_path
    db.delete(track)
    db.commit()
    _delete_raw(key)
