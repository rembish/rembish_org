"""Instagram post labeling endpoints."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, cast

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth.session import get_admin_user
from ..config import settings
from ..database import get_db
from ..models import (
    City,
    InstagramMedia,
    InstagramPost,
    TCCDestination,
    Trip,
    UNCountry,
    User,
)
from ..storage import StorageBackend, get_storage

router = APIRouter(prefix="/instagram", tags=["instagram"])

# Instagram API config
GRAPH_API_URL = "https://graph.facebook.com/v24.0"

# Storage paths (for cursor file - always local)
DATA_DIR = Path("/app/data/instagram")
CURSOR_FILE = DATA_DIR / ".pagination_cursor"


class InstagramMediaData(BaseModel):
    """Media item within a post."""

    id: int
    media_type: str
    storage_path: str | None
    order: int


class InstagramPostData(BaseModel):
    """Post data for labeling UI."""

    id: int
    ig_id: str
    caption: str | None
    media_type: str
    posted_at: str
    permalink: str
    ig_location_name: str | None
    ig_location_lat: float | None
    ig_location_lng: float | None
    media: list[InstagramMediaData]
    # Position in timeline (1 = newest)
    position: int
    total: int
    # Current labels (if any)
    un_country_id: int | None
    tcc_destination_id: int | None
    trip_id: int | None
    city_id: int | None
    is_aerial: bool | None
    is_cover: bool
    # Suggestions
    suggested_trip: dict | None
    previous_labels: dict | None


class LabelingStats(BaseModel):
    """Progress statistics."""

    total: int
    labeled: int
    skipped: int
    unlabeled: int


class LabelRequest(BaseModel):
    """Request to label a post."""

    un_country_id: int | None = None
    tcc_destination_id: int | None = None
    trip_id: int | None = None
    city_id: int | None = None
    is_aerial: bool | None = None
    is_cover: bool = False
    skip: bool = False


class LabelResponse(BaseModel):
    """Response after labeling."""

    success: bool
    ig_id: str


class PostNavigation(BaseModel):
    """Navigation info for a post."""

    prev_ig_id: str | None
    next_ig_id: str | None


class TripOption(BaseModel):
    """Trip option for manual selection."""

    id: int
    start_date: str
    end_date: str | None
    destinations: list[str]


def _get_post_position(db: Session, posted_at: datetime) -> tuple[int, int]:
    """Get position (1=newest) and total count for a post by its posted_at timestamp."""
    base_filter = InstagramPost.media_type != "VIDEO"
    total = db.query(func.count(InstagramPost.id)).filter(base_filter).scalar() or 0
    # Position = count of posts with posted_at >= this post's posted_at (including itself)
    position = (
        db.query(func.count(InstagramPost.id))
        .filter(base_filter, InstagramPost.posted_at >= posted_at)
        .scalar()
        or 1
    )
    return position, total


@router.get("/stats")
def get_labeling_stats(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> LabelingStats:
    """Get labeling progress statistics (excluding VIDEO posts)."""
    base_filter = InstagramPost.media_type != "VIDEO"
    total = db.query(func.count(InstagramPost.id)).filter(base_filter).scalar() or 0
    labeled = (
        db.query(func.count(InstagramPost.id))
        .filter(base_filter, InstagramPost.labeled_at.isnot(None))
        .scalar()
        or 0
    )
    skipped = (
        db.query(func.count(InstagramPost.id))
        .filter(base_filter, InstagramPost.skipped.is_(True))
        .scalar()
        or 0
    )
    unlabeled = total - labeled - skipped

    return LabelingStats(
        total=total,
        labeled=labeled,
        skipped=skipped,
        unlabeled=unlabeled,
    )


@router.get("/trips")
def get_trips_for_labeling(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    before_date: str | None = None,
) -> list[TripOption]:
    """Get trips for manual selection, filtered by date."""
    from datetime import timedelta

    query = db.query(Trip)

    if before_date:
        # Parse the date and filter trips relevant to the post date:
        # 1. Trips where post date falls during the trip (ongoing)
        # 2. Trips that ended within 2 months before post date (retrospective posting)
        try:
            post_date = datetime.fromisoformat(before_date).date()
            cutoff_date = post_date - timedelta(days=60)  # 2 months

            query = query.filter(
                # Trip started on or before post date
                Trip.start_date <= post_date
            ).filter(
                # AND either:
                # 1. Trip is ongoing (end_date >= post_date or end_date is NULL for single-day)
                # 2. Trip ended recently (within 2 months before post)
                ((Trip.end_date.isnot(None)) & (Trip.end_date >= cutoff_date))
                | ((Trip.end_date.is_(None)) & (Trip.start_date >= cutoff_date))
            )
        except ValueError:
            pass

    trips = query.order_by(Trip.start_date.desc()).limit(20).all()

    return [
        TripOption(
            id=trip.id,
            start_date=trip.start_date.isoformat(),
            end_date=trip.end_date.isoformat() if trip.end_date else None,
            destinations=[d.tcc_destination.name for d in trip.destinations if d.tcc_destination],
        )
        for trip in trips
    ]


@router.get("/posts/latest")
def get_latest_post(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> str | None:
    """Get the ig_id of the most recent post (by posted_at)."""
    post = (
        db.query(InstagramPost)
        .filter(InstagramPost.media_type != "VIDEO")
        .order_by(InstagramPost.posted_at.desc())
        .first()
    )
    return post.ig_id if post else None


@router.get("/posts/first-unprocessed")
def get_first_unprocessed_post(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> str | None:
    """Get the ig_id of the next unprocessed post (newest unlabeled by posted_at)."""
    post = (
        db.query(InstagramPost)
        .filter(
            InstagramPost.labeled_at.is_(None),
            InstagramPost.skipped.is_(False),
            InstagramPost.media_type != "VIDEO",
        )
        .order_by(InstagramPost.posted_at.desc())
        .first()
    )
    return post.ig_id if post else None


@router.get("/posts/first-skipped")
def get_first_skipped_post(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> str | None:
    """Get the ig_id of the first skipped post (oldest skipped)."""
    post = (
        db.query(InstagramPost)
        .filter(
            InstagramPost.skipped.is_(True),
            InstagramPost.media_type != "VIDEO",
        )
        .order_by(InstagramPost.posted_at.asc())
        .first()
    )
    return post.ig_id if post else None


@router.get("/posts/{ig_id}/nav")
def get_post_navigation(
    ig_id: str,
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> PostNavigation:
    """Get prev/next post ig_ids for navigation."""
    current = db.query(InstagramPost).filter(InstagramPost.ig_id == ig_id).first()
    if not current:
        raise HTTPException(status_code=404, detail="Post not found")

    # Previous post (newer in time)
    prev_post = (
        db.query(InstagramPost)
        .filter(
            InstagramPost.posted_at > current.posted_at,
            InstagramPost.media_type != "VIDEO",
        )
        .order_by(InstagramPost.posted_at.asc())
        .first()
    )

    # Next post (older in time)
    next_post = (
        db.query(InstagramPost)
        .filter(
            InstagramPost.posted_at < current.posted_at,
            InstagramPost.media_type != "VIDEO",
        )
        .order_by(InstagramPost.posted_at.desc())
        .first()
    )

    return PostNavigation(
        prev_ig_id=prev_post.ig_id if prev_post else None,
        next_ig_id=next_post.ig_id if next_post else None,
    )


@router.get("/posts/next")
def get_next_unlabeled_post(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> InstagramPostData | None:
    """Get the next unlabeled post (oldest first)."""
    # Find oldest unlabeled, unskipped post (skip VIDEO posts)
    post = (
        db.query(InstagramPost)
        .filter(
            InstagramPost.labeled_at.is_(None),
            InstagramPost.skipped.is_(False),
            InstagramPost.media_type != "VIDEO",
        )
        .order_by(InstagramPost.posted_at.desc())
        .first()
    )

    if not post:
        return None

    # Get media items
    media_items = (
        db.query(InstagramMedia)
        .filter(InstagramMedia.post_id == post.id)
        .order_by(InstagramMedia.media_order)
        .all()
    )

    # Find suggested trip based on post date
    # 1. Exact match: post during trip
    # 2. Recent match: post within 30 days after trip ended
    from datetime import timedelta

    suggested_trip = None
    post_date = post.posted_at.date()

    # First try: post date during trip (most recent trip first)
    # For NULL end_date, treat as single-day trip (start_date only)
    trip = (
        db.query(Trip)
        .filter(Trip.start_date <= post_date)
        .filter(
            (Trip.end_date >= post_date)
            | ((Trip.end_date.is_(None)) & (Trip.start_date == post_date))
        )
        .order_by(Trip.start_date.desc())
        .first()
    )

    # Second try: most recent trip that ended within 30 days before post
    if not trip:
        cutoff_date = post_date - timedelta(days=30)
        trip = (
            db.query(Trip)
            .filter(Trip.end_date.isnot(None))
            .filter(Trip.end_date >= cutoff_date)
            .filter(Trip.end_date < post_date)
            .order_by(Trip.end_date.desc())
            .first()
        )
    if trip:
        # Get trip destinations for display (show all for multi-region trips)
        dest_names = [d.tcc_destination.name for d in trip.destinations if d.tcc_destination]
        suggested_trip = {
            "id": trip.id,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat() if trip.end_date else None,
            "destinations": dest_names,
        }

    # Get most recently labeled post for suggestions (what you just did)
    previous_labels = None
    prev_post = (
        db.query(InstagramPost)
        .filter(InstagramPost.labeled_at.isnot(None))
        .order_by(InstagramPost.labeled_at.desc())
        .first()
    )
    if prev_post and prev_post.un_country_id:
        un_country = db.query(UNCountry).filter(UNCountry.id == prev_post.un_country_id).first()
        tcc = (
            db.query(TCCDestination)
            .filter(TCCDestination.id == prev_post.tcc_destination_id)
            .first()
            if prev_post.tcc_destination_id
            else None
        )
        city = (
            db.query(City).filter(City.id == prev_post.city_id).first()
            if prev_post.city_id
            else None
        )

        previous_labels = {
            "un_country_id": prev_post.un_country_id,
            "un_country_name": un_country.name if un_country else None,
            "tcc_destination_id": prev_post.tcc_destination_id,
            "tcc_destination_name": tcc.name if tcc else None,
            "trip_id": prev_post.trip_id,
            "city_id": prev_post.city_id,
            "city_name": city.name if city else None,
            "is_aerial": prev_post.is_aerial,
        }

    position, total = _get_post_position(db, post.posted_at)

    return InstagramPostData(
        id=post.id,
        ig_id=post.ig_id,
        caption=post.caption,
        media_type=post.media_type,
        posted_at=post.posted_at.isoformat(),
        permalink=post.permalink,
        ig_location_name=post.ig_location_name,
        ig_location_lat=float(post.ig_location_lat) if post.ig_location_lat else None,
        ig_location_lng=float(post.ig_location_lng) if post.ig_location_lng else None,
        media=[
            InstagramMediaData(
                id=m.id,
                media_type=m.media_type,
                storage_path=m.storage_path,
                order=m.media_order,
            )
            for m in media_items
        ],
        position=position,
        total=total,
        un_country_id=post.un_country_id,
        tcc_destination_id=post.tcc_destination_id,
        trip_id=post.trip_id,
        city_id=post.city_id,
        is_aerial=post.is_aerial,
        is_cover=post.is_cover,
        suggested_trip=suggested_trip,
        previous_labels=previous_labels,
    )


@router.get("/posts/{ig_id}")
def get_post_by_ig_id(
    ig_id: str,
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> InstagramPostData:
    """Get a specific post by Instagram ID for editing."""
    post = db.query(InstagramPost).filter(InstagramPost.ig_id == ig_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Get media items
    media_items = (
        db.query(InstagramMedia)
        .filter(InstagramMedia.post_id == post.id)
        .order_by(InstagramMedia.media_order)
        .all()
    )

    # For editing: show the actual linked trip, not a suggestion
    suggested_trip = None
    if post.trip_id:
        # Show the actual linked trip
        trip = db.query(Trip).filter(Trip.id == post.trip_id).first()
        if trip:
            dest_names = [d.tcc_destination.name for d in trip.destinations if d.tcc_destination]
            suggested_trip = {
                "id": trip.id,
                "start_date": trip.start_date.isoformat(),
                "end_date": trip.end_date.isoformat() if trip.end_date else None,
                "destinations": dest_names,
            }

    position, total = _get_post_position(db, post.posted_at)

    return InstagramPostData(
        id=post.id,
        ig_id=post.ig_id,
        caption=post.caption,
        media_type=post.media_type,
        posted_at=post.posted_at.isoformat(),
        permalink=post.permalink,
        ig_location_name=post.ig_location_name,
        ig_location_lat=float(post.ig_location_lat) if post.ig_location_lat else None,
        ig_location_lng=float(post.ig_location_lng) if post.ig_location_lng else None,
        media=[
            InstagramMediaData(
                id=m.id,
                media_type=m.media_type,
                storage_path=m.storage_path,
                order=m.media_order,
            )
            for m in media_items
        ],
        position=position,
        total=total,
        un_country_id=post.un_country_id,
        tcc_destination_id=post.tcc_destination_id,
        trip_id=post.trip_id,
        city_id=post.city_id,
        is_aerial=post.is_aerial,
        is_cover=post.is_cover,
        suggested_trip=suggested_trip,
        previous_labels=None,
    )


@router.post("/posts/{ig_id}/label")
def label_post(
    ig_id: str,
    data: LabelRequest,
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> LabelResponse:
    """Label a post or mark it as skipped."""
    post = db.query(InstagramPost).filter(InstagramPost.ig_id == ig_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if data.skip:
        post.skipped = True
        post.labeled_at = None  # Clear labeled status when skipping
    else:
        post.skipped = False  # Clear skipped status when labeling
        post.un_country_id = data.un_country_id
        post.tcc_destination_id = data.tcc_destination_id
        post.trip_id = data.trip_id
        post.city_id = data.city_id
        post.is_aerial = data.is_aerial
        post.labeled_at = datetime.now(UTC)

        # Handle cover photo - only one cover per trip
        if data.is_cover and data.trip_id:
            # Clear cover from other posts in same trip
            db.query(InstagramPost).filter(
                InstagramPost.trip_id == data.trip_id,
                InstagramPost.id != post.id,
                InstagramPost.is_cover.is_(True),
            ).update({"is_cover": False})
            post.is_cover = True
        else:
            post.is_cover = False

    db.commit()

    return LabelResponse(success=True, ig_id=post.ig_id)


@router.get("/media/{media_id}", response_model=None)
def get_media_file(
    media_id: int,
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> FileResponse | RedirectResponse:
    """Get media file path for serving."""

    media = db.query(InstagramMedia).filter(InstagramMedia.id == media_id).first()
    if not media or not media.storage_path:
        raise HTTPException(status_code=404, detail="Media not found")

    # If storage_path is a URL (GCS), redirect to it
    if media.storage_path.startswith("http"):
        return RedirectResponse(url=media.storage_path, status_code=302)

    # Fallback to local file serving (dev mode)
    path = Path(media.storage_path)

    # If path doesn't exist, try Docker mount path
    if not path.exists():
        # Extract filename and look in Docker mount location
        filename = path.name
        docker_path = Path("/app/data/instagram") / filename
        if docker_path.exists():
            path = docker_path
        else:
            raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path, media_type="image/jpeg")


class FetchResponse(BaseModel):
    """Response from fetch operation."""

    fetched: int
    skipped: int
    message: str


def _load_cursor() -> str | None:
    """Load saved pagination cursor."""
    if CURSOR_FILE.exists():
        try:
            data: dict[str, str] = json.loads(CURSOR_FILE.read_text())
            return data.get("next_url")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def _save_cursor(next_url: str | None) -> None:
    """Save pagination cursor for next fetch."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CURSOR_FILE.write_text(json.dumps({"next_url": next_url}))


def _api_request_with_retry(
    url: str, params: dict[str, Any] | None = None, max_retries: int = 3
) -> dict[str, Any]:
    """Make API request with retry logic."""
    import time

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params or {}, timeout=60)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff: 1s, 2s, 4s
                continue
            raise e
    # Should not reach here, but satisfy mypy
    raise last_error or RuntimeError("Request failed")


def _fetch_posts_from_api(
    limit: int, cursor_url: str | None = None
) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch posts from Instagram Graph API."""
    posts: list[dict[str, Any]] = []

    if cursor_url:
        url = cursor_url
        params: dict[str, Any] = {}
    else:
        url = f"{GRAPH_API_URL}/{settings.instagram_account_id}/media"
        params = {
            "fields": "id,caption,media_type,timestamp,permalink,location",
            "limit": min(limit, 100),
            "access_token": settings.instagram_page_token or "",
        }

    while len(posts) < limit:
        data = _api_request_with_retry(url, params if params else None)

        posts.extend(data.get("data", []))

        paging = data.get("paging", {})
        next_url = paging.get("next") if isinstance(paging, dict) else None
        if not next_url or len(posts) >= limit:
            return posts[:limit], str(next_url) if next_url else None

        url = str(next_url)
        params = {}

    return posts[:limit], None


def _fetch_carousel_children(post_id: str) -> list[dict[str, Any]]:
    """Fetch children of a carousel post."""
    url = f"{GRAPH_API_URL}/{post_id}/children"
    params: dict[str, Any] = {
        "fields": "id,media_type,media_url",
        "access_token": settings.instagram_page_token or "",
    }
    data = _api_request_with_retry(url, params)
    return cast(list[dict[str, Any]], data.get("data", []))


def _fetch_media_url(media_id: str) -> str | None:
    """Fetch media URL for a single post."""
    url = f"{GRAPH_API_URL}/{media_id}"
    params: dict[str, Any] = {
        "fields": "media_url",
        "access_token": settings.instagram_page_token or "",
    }
    data = _api_request_with_retry(url, params)
    media_url = data.get("media_url")
    return str(media_url) if media_url else None


def _download_image(
    url: str, filename: str, storage: StorageBackend
) -> tuple[str, tuple[int, int] | None]:
    """Download image, save to storage, return (storage_path, dimensions)."""
    from io import BytesIO

    from PIL import Image

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        content = response.content

        # Get dimensions from content
        dimensions: tuple[int, int] | None = None
        try:
            with Image.open(BytesIO(content)) as img:
                dimensions = img.size
        except Exception:
            pass

        # Save to storage (local or GCS)
        storage_path = storage.save(filename, content)
        return storage_path, dimensions
    except Exception:
        return "", None


def _process_single_post(db: Session, post_data: dict, storage: StorageBackend) -> bool:
    """Process a single Instagram post. Returns True if new post was added."""
    ig_id = post_data["id"]

    # Check if already exists
    existing = db.query(InstagramPost).filter(InstagramPost.ig_id == ig_id).first()
    if existing:
        return False

    # Parse location
    location = post_data.get("location", {})
    location_name = location.get("name") if location else None
    location_lat = location.get("latitude") if location else None
    location_lng = location.get("longitude") if location else None

    # Create post record
    post = InstagramPost(
        ig_id=ig_id,
        caption=post_data.get("caption"),
        media_type=post_data["media_type"],
        posted_at=datetime.fromisoformat(post_data["timestamp"].replace("+0000", "+00:00")),
        permalink=post_data["permalink"],
        ig_location_name=location_name,
        ig_location_lat=location_lat,
        ig_location_lng=location_lng,
        fetched_at=datetime.now(UTC),
    )
    db.add(post)
    db.flush()

    # Get media items
    media_items = []
    if post_data["media_type"] == "CAROUSEL_ALBUM":
        children = _fetch_carousel_children(ig_id)
        for i, child in enumerate(children):
            media_items.append(
                {
                    "ig_media_id": child["id"],
                    "media_type": child["media_type"],
                    "media_url": child.get("media_url"),
                    "order": i,
                }
            )
    else:
        media_url = _fetch_media_url(ig_id)
        media_items.append(
            {
                "ig_media_id": ig_id,
                "media_type": post_data["media_type"],
                "media_url": media_url,
                "order": 0,
            }
        )

    # Download and save media
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for item in media_items:
        if item["media_type"] == "VIDEO":
            media = InstagramMedia(
                post_id=post.id,
                ig_media_id=item["ig_media_id"],
                media_order=item["order"],
                media_type=item["media_type"],
            )
        else:
            filename = f"{item['ig_media_id']}.jpg"

            storage_path = ""
            dimensions = None
            media_url = item.get("media_url")
            if media_url:
                storage_path, dimensions = _download_image(str(media_url), filename, storage)

            media = InstagramMedia(
                post_id=post.id,
                ig_media_id=item["ig_media_id"],
                media_order=item["order"],
                media_type=item["media_type"],
                storage_path=storage_path if storage_path else None,
                width=dimensions[0] if dimensions else None,
                height=dimensions[1] if dimensions else None,
                downloaded_at=datetime.now(UTC) if storage_path else None,
            )

        db.add(media)

    return True


@router.post("/fetch")
def fetch_more_posts(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    count: int = 10,
) -> FetchResponse:
    """Fetch older posts from Instagram API (continues from cursor)."""
    if not settings.instagram_account_id or not settings.instagram_page_token:
        raise HTTPException(status_code=500, detail="Instagram API not configured")

    storage = get_storage()

    # Load cursor to continue from last position
    cursor = _load_cursor()

    # If no cursor, we need to calibrate: find the oldest post we have
    # and page until we pass it
    oldest_ig_id = None
    if not cursor:
        oldest_post = db.query(InstagramPost).order_by(InstagramPost.posted_at.asc()).first()
        if oldest_post:
            oldest_ig_id = oldest_post.ig_id

    fetched = 0
    skipped = 0
    calibrating = oldest_ig_id is not None and cursor is None
    found_oldest = False
    max_pages = 50  # Higher limit for calibration

    try:
        for _ in range(max_pages):
            posts, next_cursor = _fetch_posts_from_api(100, cursor)

            if not posts:
                _save_cursor(None)
                break

            for post_data in posts:
                ig_id = post_data["id"]

                # If calibrating, skip until we pass our oldest post
                if calibrating and not found_oldest:
                    if ig_id == oldest_ig_id:
                        found_oldest = True
                    continue

                try:
                    if _process_single_post(db, post_data, storage):
                        fetched += 1
                        if fetched >= count:
                            db.commit()
                            _save_cursor(next_cursor)
                            msg = f"Fetched {fetched} new posts"
                            if calibrating:
                                msg += f" (calibrated, skipped {skipped} existing)"
                            return FetchResponse(fetched=fetched, skipped=skipped, message=msg)
                    else:
                        skipped += 1
                except IntegrityError:
                    # Duplicate entry - rollback to clear session state and continue
                    db.rollback()
                    skipped += 1
                    continue
                except Exception:
                    # Other errors - rollback and continue
                    db.rollback()
                    skipped += 1
                    continue

            cursor = next_cursor
            if not cursor:
                break

    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Instagram API error: {e}")

    db.commit()
    _save_cursor(cursor)

    return FetchResponse(
        fetched=fetched,
        skipped=skipped,
        message=f"Fetched {fetched} new posts" + (f" (skipped {skipped})" if skipped else ""),
    )


@router.get("/fill-gaps")
def fill_gaps_stream(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    max_pages: int = 50,
) -> Any:
    """Scan through all Instagram posts and fill any gaps in the database.

    Returns a Server-Sent Events stream with progress updates.
    """
    from starlette.responses import StreamingResponse

    if not settings.instagram_account_id or not settings.instagram_page_token:
        raise HTTPException(status_code=500, detail="Instagram API not configured")

    storage = get_storage()

    def generate() -> Any:
        # Get the oldest post in DB to know when to stop
        oldest_post = db.query(InstagramPost).order_by(InstagramPost.posted_at.asc()).first()
        oldest_timestamp = None
        if oldest_post and oldest_post.posted_at:
            # Make timezone-aware for comparison with API timestamps
            if oldest_post.posted_at.tzinfo is None:
                oldest_timestamp = oldest_post.posted_at.replace(tzinfo=UTC)
            else:
                oldest_timestamp = oldest_post.posted_at

        fetched = 0
        checked = 0
        pages_fetched = 0

        url = f"{GRAPH_API_URL}/{settings.instagram_account_id}/media"
        params: dict = {
            "fields": "id,caption,media_type,timestamp,permalink,location",
            "limit": 50,
            "access_token": settings.instagram_page_token,
        }

        try:
            while pages_fetched < max_pages:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                pages_fetched += 1

                posts = data.get("data", [])
                if not posts:
                    break

                for post_data in posts:
                    checked += 1
                    post_timestamp = datetime.fromisoformat(
                        post_data["timestamp"].replace("+0000", "+00:00")
                    )

                    # If we've gone past our oldest post, we're done
                    if oldest_timestamp and post_timestamp < oldest_timestamp:
                        db.commit()
                        msg = {
                            "done": True,
                            "fetched": fetched,
                            "checked": checked,
                            "page": pages_fetched,
                        }
                        yield f"data: {json.dumps(msg)}\n\n"
                        return

                    # Check if this post exists
                    existing = (
                        db.query(InstagramPost)
                        .filter(InstagramPost.ig_id == post_data["id"])
                        .first()
                    )
                    if existing:
                        continue

                    # Post is missing - try to add it
                    try:
                        if _process_single_post(db, post_data, storage):
                            fetched += 1
                            db.commit()  # Commit each successful post
                            # Send progress update when we find a gap
                            msg = {"fetched": fetched, "checked": checked, "page": pages_fetched}
                            yield f"data: {json.dumps(msg)}\n\n"
                    except IntegrityError:
                        # Post was added by another process - that's fine
                        db.rollback()
                        continue
                    except Exception as e:
                        db.rollback()
                        # Log but continue - we want to find all gaps
                        print(f"Failed to fetch post {post_data['id']}: {e}")
                        continue

                # Send page progress update
                msg = {"fetched": fetched, "checked": checked, "page": pages_fetched}
                yield f"data: {json.dumps(msg)}\n\n"

                # Check for next page
                paging = data.get("paging", {})
                next_url = paging.get("next")
                if not next_url:
                    break

                url = next_url
                params = {}

        except requests.RequestException as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        db.commit()
        msg = {"done": True, "fetched": fetched, "checked": checked, "page": pages_fetched}
        yield f"data: {json.dumps(msg)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/sync-new")
def sync_new_posts(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    max_pages: int = 5,
) -> FetchResponse:
    """Fetch new posts from Instagram (from the beginning until we hit existing posts)."""
    if not settings.instagram_account_id or not settings.instagram_page_token:
        raise HTTPException(status_code=500, detail="Instagram API not configured")

    storage = get_storage()
    fetched = 0
    skipped = 0
    consecutive_skips = 0
    pages_fetched = 0

    url = f"{GRAPH_API_URL}/{settings.instagram_account_id}/media"
    params: dict = {
        "fields": "id,caption,media_type,timestamp,permalink,location",
        "limit": 50,
        "access_token": settings.instagram_page_token,
    }

    try:
        while pages_fetched < max_pages:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            pages_fetched += 1

            posts = data.get("data", [])
            if not posts:
                break

            for post_data in posts:
                try:
                    if _process_single_post(db, post_data, storage):
                        fetched += 1
                        consecutive_skips = 0
                    else:
                        skipped += 1
                        consecutive_skips += 1
                        # If we hit 10 consecutive existing posts, we've caught up
                        if consecutive_skips >= 10:
                            db.commit()
                            return FetchResponse(
                                fetched=fetched,
                                skipped=skipped,
                                message=f"Synced {fetched} new posts (caught up with existing)",
                            )
                except IntegrityError:
                    # Duplicate entry - rollback to clear session state and continue
                    db.rollback()
                    skipped += 1
                    consecutive_skips += 1
                    if consecutive_skips >= 10:
                        return FetchResponse(
                            fetched=fetched,
                            skipped=skipped,
                            message=f"Synced {fetched} new posts (caught up with existing)",
                        )
                    continue
                except Exception:
                    # Other errors - rollback and continue
                    db.rollback()
                    skipped += 1
                    continue

            # Check for next page
            paging = data.get("paging", {})
            next_url = paging.get("next")
            if not next_url:
                break

            url = next_url
            params = {}

    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Instagram API error: {e}")

    db.commit()

    return FetchResponse(
        fetched=fetched,
        skipped=skipped,
        message=f"Synced {fetched} new posts"
        + (f" ({skipped} already existed)" if skipped else ""),
    )
