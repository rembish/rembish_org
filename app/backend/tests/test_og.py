"""Tests for Open Graph meta tag endpoint."""

from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import (
    InstagramMedia,
    InstagramPost,
    TCCDestination,
    Trip,
    TripDestination,
    UNCountry,
)


def _make_country(db: Session, **overrides: object) -> UNCountry:
    defaults: dict[str, object] = dict(
        name="Testland",
        iso_alpha2="TL",
        iso_alpha3="TLD",
        iso_numeric="999",
        continent="Europe",
        map_region_codes="999",
        capital_lat=50.0,
        capital_lng=10.0,
    )
    defaults.update(overrides)
    country = UNCountry(**defaults)
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


def _make_tcc(db: Session, country: UNCountry, **overrides: object) -> TCCDestination:
    defaults: dict[str, object] = dict(
        name=f"{country.name} Main",
        tcc_region="EUROPE & MEDITERRANEAN",
        tcc_index=100,
        un_country_id=country.id,
    )
    defaults.update(overrides)
    dest = TCCDestination(**defaults)
    db.add(dest)
    db.commit()
    db.refresh(dest)
    return dest


def _make_trip(db: Session, **overrides: object) -> Trip:
    defaults: dict[str, object] = dict(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 10),
        trip_type="regular",
    )
    defaults.update(overrides)
    trip = Trip(**defaults)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def _link_dest(db: Session, trip: Trip, tcc: TCCDestination) -> TripDestination:
    td = TripDestination(trip_id=trip.id, tcc_destination_id=tcc.id)
    db.add(td)
    db.commit()
    db.refresh(td)
    return td


def _make_post(
    db: Session,
    trip: Trip,
    tcc: TCCDestination,
    *,
    ig_id: str = "IG_OG_1",
    is_cover: bool = False,
    labeled: bool = True,
) -> InstagramPost:
    post = InstagramPost(
        ig_id=ig_id,
        caption="Test",
        media_type="IMAGE",
        posted_at=datetime(2024, 6, 5, 12, 0, 0),
        permalink=f"https://instagram.com/p/{ig_id}",
        labeled_at=datetime(2024, 7, 1) if labeled else None,
        skipped=False,
        fetched_at=datetime(2024, 6, 5),
        trip_id=trip.id,
        tcc_destination_id=tcc.id,
        is_cover=is_cover,
        is_aerial=False,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def _make_media(
    db: Session,
    post: InstagramPost,
    *,
    media_order: int = 0,
    ig_media_id: str | None = None,
) -> InstagramMedia:
    media = InstagramMedia(
        post_id=post.id,
        ig_media_id=ig_media_id or f"M_{post.ig_id}_{media_order}",
        media_order=media_order,
        media_type="IMAGE",
        storage_path="/fake/path.jpg",
        width=1080,
        height=1080,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


# ---------------------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------------------


def test_og_root_page(client: TestClient) -> None:
    """Root path returns default OG title."""
    r = client.get("/api/v1/og", params={"path": "/"})
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert 'og:title" content="Alex Rembish' in r.text


def test_og_cv_page(client: TestClient) -> None:
    """CV path returns CV-specific OG title."""
    r = client.get("/api/v1/og", params={"path": "/cv"})
    assert r.status_code == 200
    assert "CV / Resume" in r.text


def test_og_travels_page(client: TestClient) -> None:
    """Travels path returns Travels OG title."""
    r = client.get("/api/v1/og", params={"path": "/travels"})
    assert r.status_code == 200
    assert "Travels" in r.text


def test_og_travels_subpath(client: TestClient) -> None:
    """Travels subpath (e.g. /travels/42) falls back to Travels title."""
    r = client.get("/api/v1/og", params={"path": "/travels/42"})
    assert r.status_code == 200
    assert "Travels" in r.text


def test_og_photos_albums(client: TestClient) -> None:
    """Photo albums index returns gallery title."""
    r = client.get("/api/v1/og", params={"path": "/photos/albums"})
    assert r.status_code == 200
    assert "Photo Gallery" in r.text


def test_og_photos_map(client: TestClient) -> None:
    """Photos map path returns map title."""
    r = client.get("/api/v1/og", params={"path": "/photos/map"})
    assert r.status_code == 200
    assert "Photos Map" in r.text


# ---------------------------------------------------------------------------
# Unknown / fallback
# ---------------------------------------------------------------------------


def test_og_unknown_path_returns_default(client: TestClient) -> None:
    """Unknown paths return default OG tags (not 404)."""
    r = client.get("/api/v1/og", params={"path": "/nonexistent"})
    assert r.status_code == 200
    assert "Alex Rembish" in r.text


def test_og_no_path_defaults_to_root(client: TestClient) -> None:
    """Missing path param defaults to /."""
    r = client.get("/api/v1/og")
    assert r.status_code == 200
    assert "Alex Rembish" in r.text


# ---------------------------------------------------------------------------
# Trip album
# ---------------------------------------------------------------------------


def test_og_trip_album(client: TestClient, db_session: Session) -> None:
    """Trip album OG includes destination names and date."""
    country = _make_country(db_session)
    tcc = _make_tcc(db_session, country, name="Berlin")
    trip = _make_trip(db_session)
    _link_dest(db_session, trip, tcc)
    post = _make_post(db_session, trip, tcc, is_cover=True)
    media = _make_media(db_session, post)

    r = client.get("/api/v1/og", params={"path": f"/photos/albums/{trip.id}"})
    assert r.status_code == 200
    assert "Berlin" in r.text
    assert "Jun 2024" in r.text
    assert f"/media/{media.id}" in r.text


def test_og_trip_album_nonexistent(client: TestClient) -> None:
    """Nonexistent trip album falls back to default OG."""
    r = client.get("/api/v1/og", params={"path": "/photos/albums/99999"})
    assert r.status_code == 200
    assert "Alex Rembish" in r.text


# ---------------------------------------------------------------------------
# Country photos
# ---------------------------------------------------------------------------


def test_og_country_photos(client: TestClient, db_session: Session) -> None:
    """Country photo OG includes country name."""
    country = _make_country(db_session, name="Germany")
    tcc = _make_tcc(db_session, country, name="Berlin")
    trip = _make_trip(db_session)
    _link_dest(db_session, trip, tcc)
    post = _make_post(db_session, trip, tcc)
    media = _make_media(db_session, post)

    r = client.get("/api/v1/og", params={"path": f"/photos/map/{country.id}"})
    assert r.status_code == 200
    assert "Germany" in r.text
    assert f"/media/{media.id}" in r.text


def test_og_country_nonexistent(client: TestClient) -> None:
    """Nonexistent country falls back to default OG."""
    r = client.get("/api/v1/og", params={"path": "/photos/map/99999"})
    assert r.status_code == 200
    assert "Alex Rembish" in r.text


# ---------------------------------------------------------------------------
# HTML structure
# ---------------------------------------------------------------------------


def test_og_html_has_meta_refresh(client: TestClient) -> None:
    """OG response includes meta refresh redirect for humans."""
    r = client.get("/api/v1/og", params={"path": "/"})
    assert 'http-equiv="refresh"' in r.text


def test_og_html_has_canonical_url(client: TestClient) -> None:
    """OG response includes og:url with canonical URL."""
    r = client.get("/api/v1/og", params={"path": "/cv"})
    assert 'og:url" content="https://rembish.org/cv"' in r.text


def test_og_html_has_twitter_card(client: TestClient) -> None:
    """OG response includes Twitter Card tags."""
    r = client.get("/api/v1/og", params={"path": "/"})
    assert 'twitter:card" content="summary_large_image"' in r.text
    assert 'twitter:title"' in r.text
    assert 'twitter:image"' in r.text


def test_og_html_escapes_special_chars(client: TestClient) -> None:
    """Special characters in path are HTML-escaped."""
    r = client.get("/api/v1/og", params={"path": '/<script>alert("xss")</script>'})
    assert r.status_code == 200
    assert "<script>" not in r.text
    assert "&lt;script&gt;" in r.text
