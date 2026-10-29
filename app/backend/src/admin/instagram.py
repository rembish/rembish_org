"""Instagram post labeling endpoints."""

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, cast

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth.session import get_admin_user
from ..config import settings
from ..database import get_db
from ..log_config import get_logger
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

log = get_logger(__name__)
router = APIRouter(prefix="/instagram", tags=["instagram"])

# Instagram API config
GRAPH_API_URL = "https://graph.facebook.com/v24.0"

# Cursor file — stored in /tmp (always writable, even in non-root containers)
CURSOR_FILE = Path("/tmp/.instagram_pagination_cursor")


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
    cover_media_id: int | None
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
    cover_media_id: int | None = None
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
        cover_media_id=post.cover_media_id,
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
        cover_media_id=post.cover_media_id,
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
            ).update({"is_cover": False, "cover_media_id": None})
            post.is_cover = True
            post.cover_media_id = data.cover_media_id
        else:
            post.is_cover = False
            post.cover_media_id = None

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
    """Load the saved `after` cursor of the older-posts fetch."""
    if CURSOR_FILE.exists():
        try:
            data: dict[str, str] = json.loads(CURSOR_FILE.read_text())
            return data.get("after")
        except (json.JSONDecodeError, KeyError, AttributeError):
            pass
    return None


def _save_cursor(after: str | None) -> None:
    """Save the `after` cursor for the next fetch."""
    CURSOR_FILE.write_text(json.dumps({"after": after}))


# Graph API throttling codes (app, user, page and Instagram business use case limits)
RATE_LIMIT_CODES = {4, 17, 32, 613, 80001, 80002, 80006}


class MetaAPIError(Exception):
    """A Graph API failure, described by Meta's own message.

    Never built from httpx's exception text: that includes the request URL, and the
    URL carries the access token.
    """

    def __init__(self, message: str, code: int | None = None, retry_minutes: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.retry_minutes = retry_minutes

    @property
    def rate_limited(self) -> bool:
        return self.code in RATE_LIMIT_CODES or self.retry_minutes > 0

    @property
    def hint(self) -> str:
        if self.retry_minutes:
            return f" Try again in about {self.retry_minutes} min."
        return " Try again later." if self.rate_limited else ""


def _meta_error(response: httpx.Response) -> MetaAPIError:
    try:
        error = response.json().get("error") or {}
    except ValueError:
        error = {}
    retry = 0
    try:
        usage = json.loads(response.headers.get("x-business-use-case-usage") or "{}")
        for entries in usage.values():
            for entry in entries:
                retry = max(retry, int(entry.get("estimated_time_to_regain_access") or 0))
    except (ValueError, AttributeError, TypeError):
        pass
    message = error.get("message") or response.reason_phrase
    return MetaAPIError(
        f"Instagram API {response.status_code}: {message}", error.get("code"), retry
    )


def _api_request_with_retry(
    url: str, params: dict[str, Any] | None = None, max_retries: int = 3
) -> dict[str, Any]:
    """GET a Graph API URL, retrying timeouts and connection errors; MetaAPIError otherwise."""
    import time

    for attempt in range(max_retries):
        try:
            response = httpx.get(url, params=params or {}, timeout=60)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            log.warning(
                "Instagram API request failed (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                type(e).__name__,
            )
            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff: 1s, 2s, 4s
                continue
            raise MetaAPIError(f"Instagram API unreachable ({type(e).__name__})") from None
        if response.is_error:
            error = _meta_error(response)
            log.warning("%s (code %s)", error, error.code)
            raise error
        return cast(dict[str, Any], response.json())
    raise MetaAPIError("Instagram API request failed")


MEDIA_FIELDS = "id,caption,media_type,timestamp,permalink,location"


def _media_page(limit: int, after: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
    """One page of the account's posts, newest first, and the cursor of the next page.

    Pages are requested with our own parameters plus Meta's `after` cursor. The ready-made
    `paging.next` URL fails with "(#200) Provide valid app ID" (seen October 2026), while
    the same request built from the cursor works.
    """
    params: dict[str, Any] = {
        "fields": MEDIA_FIELDS,
        "limit": limit,
        "access_token": settings.instagram_page_token or "",
    }
    if after:
        params["after"] = after
    data = _api_request_with_retry(f"{GRAPH_API_URL}/{settings.instagram_account_id}/media", params)
    paging = data.get("paging") or {}
    cursor = (paging.get("cursors") or {}).get("after") if paging.get("next") else None
    return data.get("data", []), cursor


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
        response = httpx.get(url, timeout=60)
        response.raise_for_status()
        content = response.content

        # Get dimensions from content
        dimensions: tuple[int, int] | None = None
        try:
            with Image.open(BytesIO(content)) as img:
                dimensions = img.size
        except Exception:
            log.warning("Failed to read image dimensions for %s", filename, exc_info=True)

        # Save to storage (local or GCS)
        storage_path = storage.save(filename, content)
        return storage_path, dimensions
    except Exception:
        log.error("Failed to download image %s: %s", filename, url, exc_info=True)
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

    # Download and save media (storage backend handles directory creation)
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


def _add_post(db: Session, post_data: dict, storage: StorageBackend) -> str:
    """Store one post and commit it: "added", "exists" or "failed".

    Committing each post keeps the progress of a run that stops half way. A rate limit
    is raised to stop the run; any other failure only skips the post.
    """
    try:
        added = _process_single_post(db, post_data, storage)
        db.commit()
        return "added" if added else "exists"
    except IntegrityError:
        db.rollback()  # added meanwhile by another run
        return "exists"
    except MetaAPIError as e:
        db.rollback()
        if e.rate_limited:
            raise
        log.error("Skipped Instagram post %s: %s", post_data.get("id", "unknown"), e)
        return "failed"
    except Exception:
        db.rollback()
        log.error(
            "Failed to process Instagram post %s", post_data.get("id", "unknown"), exc_info=True
        )
        return "failed"


_sync_lock = threading.Lock()


@contextmanager
def _one_sync_at_a_time() -> Iterator[None]:
    """Overlapping syncs double the memory use (two ran out of it in prod) and the quota."""
    if not _sync_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="An Instagram sync is already running")
    try:
        yield
    finally:
        _sync_lock.release()


def _require_api() -> None:
    if not settings.instagram_account_id or not settings.instagram_page_token:
        raise HTTPException(status_code=500, detail="Instagram API not configured")


def _stopped(e: MetaAPIError, verb: str, fetched: int, skipped: int) -> FetchResponse:
    """Report a run that Meta stopped: an error if nothing was saved, else what was."""
    if not fetched:
        raise HTTPException(status_code=429 if e.rate_limited else 502, detail=f"{e}.{e.hint}")
    return FetchResponse(
        fetched=fetched,
        skipped=skipped,
        message=f"{verb} new posts, then stopped: {e}.{e.hint}",
    )


@router.post("/fetch")
def fetch_more_posts(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    count: int = 10,
) -> FetchResponse:
    """Fetch older posts from Instagram API (continues from cursor)."""
    _require_api()
    with _one_sync_at_a_time():
        storage = get_storage()
        cursor = _load_cursor()

        # Without a cursor, calibrate: page until we pass the oldest post we have
        oldest_ig_id = None
        if not cursor:
            oldest_post = db.query(InstagramPost).order_by(InstagramPost.posted_at.asc()).first()
            if oldest_post:
                oldest_ig_id = oldest_post.ig_id

        fetched = 0
        skipped = 0
        calibrating = oldest_ig_id is not None
        found_oldest = False
        max_pages = 50  # Higher limit for calibration

        try:
            for _ in range(max_pages):
                # Resume from this page's cursor if we stop inside it: posts already
                # stored are skipped, the rest of the page isn't lost
                page_cursor = cursor
                posts, cursor = _media_page(100, page_cursor)
                for post_data in posts:
                    if calibrating and not found_oldest:
                        found_oldest = post_data["id"] == oldest_ig_id
                        continue
                    result = _add_post(db, post_data, storage)
                    if result != "added":
                        skipped += 1
                        continue
                    fetched += 1
                    if fetched >= count:
                        _save_cursor(page_cursor)
                        msg = f"Fetched {fetched} new posts"
                        if calibrating:
                            msg += f" (calibrated, skipped {skipped} existing)"
                        return FetchResponse(fetched=fetched, skipped=skipped, message=msg)
                if not cursor:
                    break
        except MetaAPIError as e:
            _save_cursor(page_cursor)
            return _stopped(e, f"Fetched {fetched}", fetched, skipped)

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

    _require_api()
    storage = get_storage()

    def event(msg: dict[str, Any]) -> str:
        return f"data: {json.dumps(msg)}\n\n"

    def generate() -> Any:
        if not _sync_lock.acquire(blocking=False):
            yield event({"error": "An Instagram sync is already running"})
            return
        try:
            yield from scan()
        finally:
            _sync_lock.release()

    def scan() -> Any:
        # The oldest post in the DB tells us when to stop
        oldest_post = db.query(InstagramPost).order_by(InstagramPost.posted_at.asc()).first()
        oldest_timestamp = None
        if oldest_post and oldest_post.posted_at:
            # Make timezone-aware for comparison with API timestamps
            oldest_timestamp = oldest_post.posted_at
            if oldest_timestamp.tzinfo is None:
                oldest_timestamp = oldest_timestamp.replace(tzinfo=UTC)

        fetched = 0
        checked = 0
        pages_fetched = 0
        cursor: str | None = None

        try:
            while pages_fetched < max_pages:
                posts, cursor = _media_page(50, cursor)
                pages_fetched += 1
                if not posts:
                    break

                for post_data in posts:
                    checked += 1
                    post_timestamp = datetime.fromisoformat(
                        post_data["timestamp"].replace("+0000", "+00:00")
                    )
                    # Past our oldest post: done
                    if oldest_timestamp and post_timestamp < oldest_timestamp:
                        yield event(
                            {
                                "done": True,
                                "fetched": fetched,
                                "checked": checked,
                                "page": pages_fetched,
                            }
                        )
                        return
                    if _add_post(db, post_data, storage) == "added":
                        fetched += 1
                        # Progress update whenever a gap is filled
                        yield event({"fetched": fetched, "checked": checked, "page": pages_fetched})

                yield event({"fetched": fetched, "checked": checked, "page": pages_fetched})
                if not cursor:
                    break
        except MetaAPIError as e:
            yield event(
                {"error": f"{e}.{e.hint}" + (f" Filled {fetched} gaps first." if fetched else "")}
            )
            return

        yield event({"done": True, "fetched": fetched, "checked": checked, "page": pages_fetched})

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/sync-new")
def sync_new_posts(
    _user: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    max_pages: int = 20,
) -> FetchResponse:
    """Fetch the posts newer than the newest one stored.

    Lists them first (one call per 50 posts), then stores them oldest first: a run that
    Meta stops part way leaves no gap, so the next run simply continues.
    """
    _require_api()
    with _one_sync_at_a_time():
        storage = get_storage()
        newest = db.query(func.max(InstagramPost.posted_at)).scalar()
        if newest is not None and newest.tzinfo is None:
            newest = newest.replace(tzinfo=UTC)

        backlog: list[dict[str, Any]] = []
        fetched = 0
        skipped = 0
        try:
            cursor: str | None = None
            caught_up = False
            for _ in range(max_pages):
                posts, cursor = _media_page(50, cursor)
                for post_data in posts:
                    posted = datetime.fromisoformat(
                        post_data["timestamp"].replace("+0000", "+00:00")
                    )
                    if newest is not None and posted < newest:
                        caught_up = True
                        break
                    backlog.append(post_data)
                if caught_up or not posts or not cursor:
                    break
            if newest is not None and not caught_up and cursor:
                log.warning("Instagram sync: more than %d new posts listed", len(backlog))

            for post_data in reversed(backlog):
                if _add_post(db, post_data, storage) == "added":
                    fetched += 1
                else:
                    skipped += 1
        except MetaAPIError as e:
            return _stopped(e, f"Synced {fetched} of {len(backlog)}", fetched, skipped)

        return FetchResponse(
            fetched=fetched,
            skipped=skipped,
            message=f"Synced {fetched} new posts"
            + (f" ({skipped} already existed or failed)" if skipped else ""),
        )
