"""Open Graph meta tag endpoint for link preview unfurling."""

import html
import re

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import (
    InstagramMedia,
    InstagramPost,
    TCCDestination,
    Trip,
    TripDestination,
    UNCountry,
)

router = APIRouter(tags=["og"])

SITE_NAME = "rembish.org"
BASE_URL = "https://rembish.org"
DEFAULT_IMAGE = f"{BASE_URL}/hero-bg.jpg"
DEFAULT_TITLE = "Alex Rembish \u2014 Software Engineer"
DEFAULT_DESCRIPTION = "Alex Rembish - Software Engineer"
IMAGE_WIDTH = "1920"
IMAGE_HEIGHT = "1053"

# Static page titles
STATIC_PAGES: dict[str, str] = {
    "/": DEFAULT_TITLE,
    "/cv": "CV / Resume \u2014 Alex Rembish",
    "/projects": "Projects \u2014 Alex Rembish",
    "/contact": "Contact \u2014 Alex Rembish",
    "/changelog": f"Changelog \u2014 {SITE_NAME}",
    "/travels": "Travels \u2014 Alex Rembish",
    "/photos/albums": "Photo Gallery \u2014 Alex Rembish",
    "/photos/map": "Photos Map \u2014 Alex Rembish",
}

# Patterns for dynamic pages
TRIP_ALBUM_RE = re.compile(r"^/photos/albums/(\d+)$")
COUNTRY_PHOTOS_RE = re.compile(r"^/photos/map/(\d+)$")


def _get_trip_thumbnail(db: Session, trip_id: int) -> int | None:
    """Get cover media ID for a trip (simplified single-trip version)."""
    # 1) Cover post with explicit cover_media_id
    cover_post = (
        db.query(InstagramPost)
        .join(InstagramMedia, InstagramMedia.post_id == InstagramPost.id)
        .filter(
            InstagramPost.trip_id == trip_id,
            InstagramPost.is_cover.is_(True),
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
            InstagramMedia.media_type != "VIDEO",
        )
        .first()
    )
    if cover_post:
        if cover_post.cover_media_id:
            return cover_post.cover_media_id
        first = (
            db.query(InstagramMedia.id)
            .filter(
                InstagramMedia.post_id == cover_post.id,
                InstagramMedia.media_type != "VIDEO",
            )
            .order_by(InstagramMedia.media_order)
            .first()
        )
        if first:
            return int(first[0])

    # 2) Fallback: most recent labeled post
    recent = (
        db.query(InstagramPost)
        .join(InstagramMedia, InstagramMedia.post_id == InstagramPost.id)
        .filter(
            InstagramPost.trip_id == trip_id,
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
            InstagramMedia.media_type != "VIDEO",
        )
        .order_by(InstagramPost.posted_at.desc())
        .first()
    )
    if recent:
        first = (
            db.query(InstagramMedia.id)
            .filter(
                InstagramMedia.post_id == recent.id,
                InstagramMedia.media_type != "VIDEO",
            )
            .order_by(InstagramMedia.media_order)
            .first()
        )
        if first:
            return int(first[0])

    return None


def _get_country_thumbnail(db: Session, un_country_id: int) -> int | None:
    """Get cover media ID for a country's photos."""
    # 1) Cover post for this country
    cover = (
        db.query(InstagramPost)
        .join(TCCDestination, InstagramPost.tcc_destination_id == TCCDestination.id)
        .join(InstagramMedia, InstagramMedia.post_id == InstagramPost.id)
        .filter(
            TCCDestination.un_country_id == un_country_id,
            InstagramPost.is_cover.is_(True),
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
            InstagramMedia.media_type != "VIDEO",
        )
        .order_by(InstagramPost.posted_at.desc())
        .first()
    )
    if cover:
        if cover.cover_media_id:
            return cover.cover_media_id
        first = (
            db.query(InstagramMedia.id)
            .filter(
                InstagramMedia.post_id == cover.id,
                InstagramMedia.media_type != "VIDEO",
            )
            .order_by(InstagramMedia.media_order)
            .first()
        )
        if first:
            return int(first[0])

    # 2) Fallback: most recent post
    recent = (
        db.query(InstagramPost)
        .join(TCCDestination, InstagramPost.tcc_destination_id == TCCDestination.id)
        .join(InstagramMedia, InstagramMedia.post_id == InstagramPost.id)
        .filter(
            TCCDestination.un_country_id == un_country_id,
            InstagramPost.labeled_at.isnot(None),
            InstagramPost.skipped.is_(False),
            InstagramMedia.media_type != "VIDEO",
        )
        .order_by(InstagramPost.posted_at.desc())
        .first()
    )
    if recent:
        first = (
            db.query(InstagramMedia.id)
            .filter(
                InstagramMedia.post_id == recent.id,
                InstagramMedia.media_type != "VIDEO",
            )
            .order_by(InstagramMedia.media_order)
            .first()
        )
        if first:
            return int(first[0])

    return None


def _render_og_html(
    title: str,
    description: str,
    image: str,
    url: str,
    image_width: str = IMAGE_WIDTH,
    image_height: str = IMAGE_HEIGHT,
) -> str:
    """Render minimal HTML with OG + Twitter Card meta tags."""
    t = html.escape(title)
    d = html.escape(description)
    i = html.escape(image)
    u = html.escape(url)
    iw = html.escape(image_width)
    ih = html.escape(image_height)
    sn = html.escape(SITE_NAME)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{t}</title>
<meta property="og:type" content="website">
<meta property="og:site_name" content="{sn}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{u}">
<meta property="og:image" content="{i}">
<meta property="og:image:width" content="{iw}">
<meta property="og:image:height" content="{ih}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{i}">
<meta http-equiv="refresh" content="0;url={u}">
</head>
<body><p>Redirecting to <a href="{u}">{u}</a>...</p></body>
</html>"""


def _resolve_path(path: str, db: Session) -> tuple[str, str, str]:
    """Resolve a path to (title, description, image_url)."""
    # Normalize path
    path = path.rstrip("/") or "/"

    # Static pages
    if path in STATIC_PAGES:
        return STATIC_PAGES[path], DEFAULT_DESCRIPTION, DEFAULT_IMAGE

    # Travels sub-paths (e.g. /travels/42)
    if path.startswith("/travels"):
        return STATIC_PAGES["/travels"], DEFAULT_DESCRIPTION, DEFAULT_IMAGE

    # Trip album: /photos/albums/:id
    match = TRIP_ALBUM_RE.match(path)
    if match:
        trip_id = int(match.group(1))
        trip = (
            db.query(Trip)
            .options(joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination))
            .filter(Trip.id == trip_id)
            .first()
        )
        if trip:
            destinations = [
                td.tcc_destination.name for td in trip.destinations if td.tcc_destination
            ]
            dest_str = ", ".join(destinations) if destinations else "Trip"
            date_str = trip.start_date.strftime("%b %Y")
            title = f"{dest_str} ({date_str}) \u2014 Photos"
            description = f"Photo album from {dest_str}"

            media_id = _get_trip_thumbnail(db, trip_id)
            image = (
                f"{BASE_URL}/api/v1/travels/photos/media/{media_id}" if media_id else DEFAULT_IMAGE
            )
            return title, description, image

        return DEFAULT_TITLE, DEFAULT_DESCRIPTION, DEFAULT_IMAGE

    # Country photos: /photos/map/:id
    match = COUNTRY_PHOTOS_RE.match(path)
    if match:
        country_id = int(match.group(1))
        country = db.query(UNCountry).filter(UNCountry.id == country_id).first()
        if country:
            title = f"{country.name} \u2014 Photos"
            description = f"Photos from {country.name}"

            media_id = _get_country_thumbnail(db, country_id)
            image = (
                f"{BASE_URL}/api/v1/travels/photos/media/{media_id}" if media_id else DEFAULT_IMAGE
            )
            return title, description, image

        return DEFAULT_TITLE, DEFAULT_DESCRIPTION, DEFAULT_IMAGE

    # Fallback
    return DEFAULT_TITLE, DEFAULT_DESCRIPTION, DEFAULT_IMAGE


@router.get("/og")
def get_og_tags(path: str = "/", db: Session = Depends(get_db)) -> HTMLResponse:
    """Return minimal HTML with Open Graph meta tags for link preview bots."""
    title, description, image = _resolve_path(path, db)
    canonical_url = f"{BASE_URL}{path.rstrip('/') or '/'}"

    content = _render_og_html(
        title=title,
        description=description,
        image=image,
        url=canonical_url,
    )
    return HTMLResponse(content=content)
