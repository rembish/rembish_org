"""Public photos endpoints for displaying trip photos."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user
from ..database import get_db
from ..models import (
    InstagramMedia,
    InstagramPost,
    Trip,
    TripDestination,
    User,
)

router = APIRouter(prefix="/photos", tags=["photos"])


class PhotoTripSummary(BaseModel):
    """Summary of a trip with photos."""

    trip_id: int
    start_date: str
    end_date: str | None
    destinations: list[str]
    photo_count: int
    thumbnail_media_id: int
    is_hidden: bool = False


class PhotosYearGroup(BaseModel):
    """Photos grouped by year."""

    year: int
    trips: list[PhotoTripSummary]


class PhotosIndexResponse(BaseModel):
    """Response for photos index."""

    years: list[PhotosYearGroup]
    total_photos: int
    total_trips: int


class PhotoData(BaseModel):
    """Individual photo data."""

    ig_id: str
    media_id: int
    caption: str | None
    posted_at: str
    is_aerial: bool
    is_cover: bool
    destination: str | None
    permalink: str | None


class TripPhotosResponse(BaseModel):
    """Response for trip photos detail."""

    trip_id: int
    start_date: str
    end_date: str | None
    destinations: list[str]
    photos: list[PhotoData]


class SetCoverResponse(BaseModel):
    """Response for setting cover photo."""

    success: bool
    trip_id: int
    media_id: int


class ToggleHiddenResponse(BaseModel):
    """Response for toggling trip visibility."""

    success: bool
    trip_id: int
    is_hidden: bool


def _batch_get_thumbnail_media_ids(db: Session, trip_ids: list[int]) -> dict[int, int]:
    """Get thumbnail media IDs for multiple trips in batch.

    Returns a dict of trip_id -> media_id. Trips without valid thumbnails
    are omitted.
    """
    if not trip_ids:
        return {}

    result: dict[int, int] = {}

    # 1) Cover posts: trips that have an explicit cover photo
    cover_posts = (
        db.query(InstagramPost)
        .join(InstagramMedia, InstagramMedia.post_id == InstagramPost.id)
        .filter(
            InstagramPost.trip_id.in_(trip_ids),
            InstagramPost.is_cover.is_(True),
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
            InstagramMedia.media_type != "VIDEO",
        )
        .all()
    )

    cover_post_ids: list[int] = []
    for post in cover_posts:
        if post.trip_id is None or post.trip_id in result:
            continue
        if post.cover_media_id:
            result[post.trip_id] = post.cover_media_id
        else:
            cover_post_ids.append(post.id)

    # Get first non-video media for cover posts without cover_media_id
    if cover_post_ids:
        cover_media = (
            db.query(InstagramMedia)
            .filter(
                InstagramMedia.post_id.in_(cover_post_ids),
                InstagramMedia.media_type != "VIDEO",
            )
            .order_by(InstagramMedia.post_id, InstagramMedia.media_order)
            .all()
        )
        # Map post_id -> first media, then map back to trip_id
        post_to_media: dict[int, int] = {}
        for m in cover_media:
            if m.post_id not in post_to_media:
                post_to_media[m.post_id] = m.id
        post_id_to_trip: dict[int, int] = {
            p.id: p.trip_id
            for p in cover_posts
            if p.trip_id is not None and p.trip_id not in result
        }
        for post_id, media_id in post_to_media.items():
            trip_id = post_id_to_trip.get(post_id)
            if trip_id and trip_id not in result:
                result[trip_id] = media_id

    # 2) Fallback: trips without covers — use most recent labeled post
    remaining = [tid for tid in trip_ids if tid not in result]
    if not remaining:
        return result

    # Get the most recent labeled post per remaining trip
    recent_posts = (
        db.query(InstagramPost)
        .join(InstagramMedia, InstagramMedia.post_id == InstagramPost.id)
        .filter(
            InstagramPost.trip_id.in_(remaining),
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
            InstagramMedia.media_type != "VIDEO",
        )
        .order_by(
            InstagramPost.trip_id,
            InstagramPost.posted_at.desc(),
        )
        .all()
    )

    # Pick first (most recent) post per trip
    recent_post_ids: list[int] = []
    seen_trips: set[int] = set()
    recent_post_trip_map: dict[int, int] = {}
    for post in recent_posts:
        if post.trip_id is not None and post.trip_id not in seen_trips:
            seen_trips.add(post.trip_id)
            recent_post_ids.append(post.id)
            recent_post_trip_map[post.id] = post.trip_id

    if recent_post_ids:
        fallback_media = (
            db.query(InstagramMedia)
            .filter(
                InstagramMedia.post_id.in_(recent_post_ids),
                InstagramMedia.media_type != "VIDEO",
            )
            .order_by(InstagramMedia.post_id, InstagramMedia.media_order)
            .all()
        )
        fb_post_to_media: dict[int, int] = {}
        for m in fallback_media:
            if m.post_id not in fb_post_to_media:
                fb_post_to_media[m.post_id] = m.id
        for post_id, media_id in fb_post_to_media.items():
            trip_id = recent_post_trip_map.get(post_id)
            if trip_id and trip_id not in result:
                result[trip_id] = media_id

    return result


@router.get("", response_model=PhotosIndexResponse)
def get_photos_index(
    db: Session = Depends(get_db),
    show_hidden: bool = False,
) -> PhotosIndexResponse:
    """Get all trips with labeled photos, grouped by year."""
    # Get trips with photo counts
    trips_with_photos = (
        db.query(
            Trip.id.label("trip_id"),
            func.count(InstagramMedia.id).label("photo_count"),
        )
        .join(InstagramPost, InstagramPost.trip_id == Trip.id)
        .join(InstagramMedia, InstagramMedia.post_id == InstagramPost.id)
        .filter(
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
            InstagramMedia.media_type != "VIDEO",
        )
        .group_by(Trip.id)
        .subquery()
    )

    # Get trip details with photo counts
    query = (
        db.query(
            Trip,
            trips_with_photos.c.photo_count,
        )
        .join(trips_with_photos, Trip.id == trips_with_photos.c.trip_id)
        .options(joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination))
    )

    # Filter hidden trips unless show_hidden is True
    if not show_hidden:
        query = query.filter(Trip.hidden_from_photos.is_(False))

    trips_data = query.order_by(Trip.start_date.desc()).all()

    # Batch-load thumbnails for all trips at once
    all_trip_ids = [trip.id for trip, _ in trips_data]
    thumbnail_map = _batch_get_thumbnail_media_ids(db, all_trip_ids)

    # Group by year
    years_dict: dict[int, list[PhotoTripSummary]] = {}
    total_photos = 0
    total_trips = 0

    for trip, photo_count in trips_data:
        thumbnail_id = thumbnail_map.get(trip.id)
        if thumbnail_id is None:
            continue  # Skip trips without valid thumbnails

        year = trip.start_date.year
        destinations = [td.tcc_destination.name for td in trip.destinations if td.tcc_destination]

        trip_summary = PhotoTripSummary(
            trip_id=trip.id,
            start_date=trip.start_date.isoformat(),
            end_date=trip.end_date.isoformat() if trip.end_date else None,
            destinations=destinations,
            photo_count=photo_count,
            thumbnail_media_id=thumbnail_id,
            is_hidden=trip.hidden_from_photos,
        )

        if year not in years_dict:
            years_dict[year] = []
        years_dict[year].append(trip_summary)

        total_photos += photo_count
        total_trips += 1

    # Convert to response format (sorted by year descending)
    years = [
        PhotosYearGroup(year=year, trips=trips)
        for year, trips in sorted(years_dict.items(), reverse=True)
    ]

    return PhotosIndexResponse(
        years=years,
        total_photos=total_photos,
        total_trips=total_trips,
    )


@router.get("/{trip_id}", response_model=TripPhotosResponse)
def get_trip_photos(
    trip_id: int,
    db: Session = Depends(get_db),
) -> TripPhotosResponse:
    """Get all photos for a specific trip."""
    # Get trip with destinations
    trip = (
        db.query(Trip)
        .options(joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination))
        .filter(Trip.id == trip_id)
        .first()
    )

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Get all labeled photos for this trip
    posts = (
        db.query(InstagramPost)
        .options(joinedload(InstagramPost.media), joinedload(InstagramPost.tcc_destination))
        .filter(
            InstagramPost.trip_id == trip_id,
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
        )
        .order_by(InstagramPost.posted_at.desc())
        .all()
    )

    # Build photo list (each media item is a separate photo)
    photos: list[PhotoData] = []
    for post in posts:
        for media in post.media:
            if media.media_type == "VIDEO":
                continue
            photos.append(
                PhotoData(
                    ig_id=post.ig_id,
                    media_id=media.id,
                    caption=post.caption,
                    posted_at=post.posted_at.isoformat(),
                    is_aerial=post.is_aerial or False,
                    is_cover=post.is_cover
                    and (media.id == post.cover_media_id if post.cover_media_id else True),
                    destination=post.tcc_destination.name if post.tcc_destination else None,
                    permalink=post.permalink,
                )
            )

    destinations = [td.tcc_destination.name for td in trip.destinations if td.tcc_destination]

    return TripPhotosResponse(
        trip_id=trip.id,
        start_date=trip.start_date.isoformat(),
        end_date=trip.end_date.isoformat() if trip.end_date else None,
        destinations=destinations,
        photos=photos,
    )


@router.post("/{trip_id}/cover/{media_id}", response_model=SetCoverResponse)
def set_cover_photo(
    trip_id: int,
    media_id: int,
    _admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> SetCoverResponse:
    """Set a photo as the cover for a trip (admin only)."""
    # Verify the media belongs to a labeled post in this trip
    media = (
        db.query(InstagramMedia)
        .join(InstagramPost, InstagramPost.id == InstagramMedia.post_id)
        .filter(
            InstagramMedia.id == media_id,
            InstagramPost.trip_id == trip_id,
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
        )
        .first()
    )

    if not media:
        raise HTTPException(status_code=404, detail="Photo not found in this trip")

    # Clear cover from all posts in this trip
    db.query(InstagramPost).filter(
        InstagramPost.trip_id == trip_id,
        InstagramPost.is_cover.is_(True),
    ).update({"is_cover": False, "cover_media_id": None})

    # Set the new cover with specific media
    post = db.query(InstagramPost).filter(InstagramPost.id == media.post_id).first()
    if post:
        post.is_cover = True
        post.cover_media_id = media_id

    db.commit()

    return SetCoverResponse(success=True, trip_id=trip_id, media_id=media_id)


@router.post("/{trip_id}/toggle-hidden", response_model=ToggleHiddenResponse)
def toggle_trip_hidden(
    trip_id: int,
    _admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> ToggleHiddenResponse:
    """Toggle whether a trip is hidden from photos page (admin only)."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.hidden_from_photos = not trip.hidden_from_photos
    db.commit()

    return ToggleHiddenResponse(
        success=True,
        trip_id=trip_id,
        is_hidden=trip.hidden_from_photos,
    )


@router.get("/media/{media_id}", response_model=None)
def get_public_media_file(
    media_id: int,
    db: Session = Depends(get_db),
) -> FileResponse | RedirectResponse:
    """Serve a media file (public, only for labeled non-skipped photos)."""
    # Get media with associated post
    media = (
        db.query(InstagramMedia)
        .join(InstagramPost, InstagramPost.id == InstagramMedia.post_id)
        .filter(
            InstagramMedia.id == media_id,
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
        )
        .first()
    )

    if not media or not media.storage_path:
        raise HTTPException(status_code=404, detail="Media not found")

    # If storage_path is a URL (GCS), redirect to it
    if media.storage_path.startswith("http"):
        return RedirectResponse(url=media.storage_path, status_code=302)

    # Fallback to local file serving (dev mode)
    path = Path(media.storage_path)

    # If path doesn't exist, try Docker mount path
    if not path.exists():
        filename = path.name
        docker_path = Path("/app/data/instagram") / filename
        if docker_path.exists():
            path = docker_path
        else:
            raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path, media_type="image/jpeg")
