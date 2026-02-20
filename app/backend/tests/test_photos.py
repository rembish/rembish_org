"""Tests for public photos endpoints."""

from fastapi.testclient import TestClient


def test_photos_index_returns_structure(client: TestClient) -> None:
    """Photos index should return years/trips structure."""
    response = client.get("/api/v1/travels/photos")
    assert response.status_code == 200
    data = response.json()
    assert "years" in data
    assert "total_photos" in data
    assert "total_trips" in data
    assert isinstance(data["years"], list)
    assert data["total_photos"] == 0
    assert data["total_trips"] == 0


def test_photos_trip_not_found(client: TestClient) -> None:
    """Trip photos should return 404 for missing trip."""
    response = client.get("/api/v1/travels/photos/99999")
    assert response.status_code == 404


def test_photos_index_no_auth_required(client: TestClient) -> None:
    """Photos endpoints are public - no auth needed."""
    response = client.get("/api/v1/travels/photos")
    assert response.status_code == 200


def test_photo_map_returns_structure(client: TestClient) -> None:
    """Photo map should return countries list and total."""
    response = client.get("/api/v1/travels/photos/map")
    assert response.status_code == 200
    data = response.json()
    assert "countries" in data
    assert "total_photos" in data
    assert isinstance(data["countries"], list)
    assert data["total_photos"] == 0


def test_photo_map_no_auth_required(client: TestClient) -> None:
    """Photo map endpoint is public."""
    response = client.get("/api/v1/travels/photos/map")
    assert response.status_code == 200


def test_country_photos_not_found(client: TestClient) -> None:
    """Country photos should return 404 for missing country."""
    response = client.get("/api/v1/travels/photos/country/99999")
    assert response.status_code == 404


def test_country_photos_returns_structure(client: TestClient) -> None:
    """Country photos should return proper structure for existing country."""
    from sqlalchemy.orm import Session

    from src.database import get_db
    from src.main import app
    from src.models import UNCountry

    # Get the db session from the override
    db: Session = next(app.dependency_overrides[get_db]())
    country = UNCountry(
        name="Testland",
        iso_alpha2="TL",
        iso_alpha3="TLD",
        iso_numeric="999",
        continent="Europe",
        map_region_codes="999",
        capital_lat=50.0,
        capital_lng=10.0,
    )
    db.add(country)
    db.commit()
    db.refresh(country)

    response = client.get(f"/api/v1/travels/photos/country/{country.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["un_country_id"] == country.id
    assert data["country_name"] == "Testland"
    assert data["iso_alpha2"] == "TL"
    assert data["photo_count"] == 0
    assert isinstance(data["trips"], list)


# ---------------------------------------------------------------------------
# Helper factories for seeding test data
# ---------------------------------------------------------------------------


def _make_country(db: "Session", **overrides: object) -> "UNCountry":
    """Create and persist a UNCountry record."""
    from src.models import UNCountry

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


def _make_tcc_destination(
    db: "Session", un_country: "UNCountry", **overrides: object
) -> "TCCDestination":
    from src.models import TCCDestination

    defaults: dict[str, object] = dict(
        name=f"{un_country.name} Main",
        tcc_region="EUROPE & MEDITERRANEAN",
        tcc_index=100,
        un_country_id=un_country.id,
    )
    defaults.update(overrides)
    dest = TCCDestination(**defaults)
    db.add(dest)
    db.commit()
    db.refresh(dest)
    return dest


def _make_trip(db: "Session", **overrides: object) -> "Trip":
    from datetime import date

    from src.models import Trip

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


def _link_trip_destination(
    db: "Session", trip: "Trip", tcc_dest: "TCCDestination"
) -> "TripDestination":
    from src.models import TripDestination

    td = TripDestination(trip_id=trip.id, tcc_destination_id=tcc_dest.id)
    db.add(td)
    db.commit()
    db.refresh(td)
    return td


def _make_post(
    db: "Session",
    trip: "Trip | None" = None,
    tcc_dest: "TCCDestination | None" = None,
    country: "UNCountry | None" = None,
    *,
    labeled: bool = True,
    is_cover: bool = False,
    is_hidden: bool = False,
    ig_id: str = "IG_001",
    posted_at: "datetime | None" = None,
    media_type: str = "IMAGE",
) -> "InstagramPost":
    from datetime import datetime

    from src.models import InstagramPost

    post = InstagramPost(
        ig_id=ig_id,
        caption="Test caption",
        media_type=media_type,
        posted_at=posted_at or datetime(2024, 6, 5, 12, 0, 0),
        permalink=f"https://instagram.com/p/{ig_id}",
        labeled_at=datetime(2024, 7, 1) if labeled else None,
        skipped=False,
        fetched_at=datetime(2024, 6, 5, 12, 0, 0),
        trip_id=trip.id if trip else None,
        tcc_destination_id=tcc_dest.id if tcc_dest else None,
        un_country_id=country.id if country else None,
        is_cover=is_cover,
        is_aerial=False,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def _make_media(
    db: "Session",
    post: "InstagramPost",
    *,
    media_type: str = "IMAGE",
    media_order: int = 0,
    ig_media_id: str | None = None,
) -> "InstagramMedia":
    from src.models import InstagramMedia

    media = InstagramMedia(
        post_id=post.id,
        ig_media_id=ig_media_id or f"MEDIA_{post.ig_id}_{media_order}",
        media_order=media_order,
        media_type=media_type,
        storage_path="/fake/path.jpg",
        width=1080,
        height=1080,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def _seed_full_photo_set(db: "Session") -> dict:
    """Create a complete set of related records suitable for most photo tests.

    Returns a dict with all created objects for easy reference.
    """
    country = _make_country(db)
    tcc_dest = _make_tcc_destination(db, country)
    trip = _make_trip(db)
    _link_trip_destination(db, trip, tcc_dest)

    post = _make_post(db, trip=trip, tcc_dest=tcc_dest, country=country, ig_id="IG_100")
    media = _make_media(db, post)

    return dict(
        country=country,
        tcc_dest=tcc_dest,
        trip=trip,
        post=post,
        media=media,
    )


# ---------------------------------------------------------------------------
# 1. Photo index with labeled posts
# ---------------------------------------------------------------------------


def test_photos_index_with_data(client: TestClient, db_session: "Session") -> None:
    """Photo index returns year groups with trip summaries when data exists."""
    from sqlalchemy.orm import Session

    seed = _seed_full_photo_set(db_session)

    response = client.get("/api/v1/travels/photos")
    assert response.status_code == 200
    data = response.json()

    assert data["total_photos"] == 1
    assert data["total_trips"] == 1
    assert len(data["years"]) == 1

    year_group = data["years"][0]
    assert year_group["year"] == 2024
    assert len(year_group["trips"]) == 1

    trip_summary = year_group["trips"][0]
    assert trip_summary["trip_id"] == seed["trip"].id
    assert trip_summary["photo_count"] == 1
    assert trip_summary["thumbnail_media_id"] == seed["media"].id
    assert trip_summary["start_date"] == "2024-06-01"
    assert trip_summary["end_date"] == "2024-06-10"
    assert seed["tcc_dest"].name in trip_summary["destinations"]


def test_photos_index_multiple_years(client: TestClient, db_session: "Session") -> None:
    """Photo index groups trips by year, sorted descending."""
    from datetime import date

    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)

    trip_2023 = _make_trip(
        db_session, start_date=date(2023, 3, 1), end_date=date(2023, 3, 10)
    )
    trip_2024 = _make_trip(
        db_session, start_date=date(2024, 8, 1), end_date=date(2024, 8, 10)
    )
    _link_trip_destination(db_session, trip_2023, tcc_dest)
    _link_trip_destination(db_session, trip_2024, tcc_dest)

    post_2023 = _make_post(
        db_session,
        trip=trip_2023,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_2023",
    )
    _make_media(db_session, post_2023)

    post_2024 = _make_post(
        db_session,
        trip=trip_2024,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_2024",
    )
    _make_media(db_session, post_2024)

    response = client.get("/api/v1/travels/photos")
    data = response.json()

    assert data["total_trips"] == 2
    assert data["total_photos"] == 2
    assert len(data["years"]) == 2
    # Most recent year first
    assert data["years"][0]["year"] == 2024
    assert data["years"][1]["year"] == 2023


def test_photos_index_multiple_media_per_post(
    client: TestClient, db_session: "Session"
) -> None:
    """Photo count sums all non-video media, not just posts."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_MULTI",
        media_type="CAROUSEL_ALBUM",
    )
    _make_media(db_session, post, media_order=0, ig_media_id="M1")
    _make_media(db_session, post, media_order=1, ig_media_id="M2")
    _make_media(db_session, post, media_order=2, ig_media_id="M3")

    response = client.get("/api/v1/travels/photos")
    data = response.json()
    assert data["total_photos"] == 3
    assert data["years"][0]["trips"][0]["photo_count"] == 3


def test_photos_index_excludes_unlabeled_posts(
    client: TestClient, db_session: "Session"
) -> None:
    """Unlabeled posts (labeled_at is None) are excluded from the index."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    # One labeled, one not
    labeled = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_LABELED",
        labeled=True,
    )
    _make_media(db_session, labeled)

    unlabeled = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_UNLABELED",
        labeled=False,
    )
    _make_media(db_session, unlabeled)

    response = client.get("/api/v1/travels/photos")
    data = response.json()
    assert data["total_photos"] == 1


def test_photos_index_excludes_video_media(
    client: TestClient, db_session: "Session"
) -> None:
    """VIDEO media items are excluded from photo counts."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_VID",
        media_type="CAROUSEL_ALBUM",
    )
    _make_media(db_session, post, media_order=0, media_type="IMAGE", ig_media_id="IMG1")
    _make_media(db_session, post, media_order=1, media_type="VIDEO", ig_media_id="VID1")

    response = client.get("/api/v1/travels/photos")
    data = response.json()
    assert data["total_photos"] == 1


# ---------------------------------------------------------------------------
# 2. Trip photos
# ---------------------------------------------------------------------------


def test_trip_photos_returns_photos(client: TestClient, db_session: "Session") -> None:
    """Trip photos endpoint returns labeled photos for a specific trip."""
    seed = _seed_full_photo_set(db_session)

    response = client.get(f"/api/v1/travels/photos/{seed['trip'].id}")
    assert response.status_code == 200
    data = response.json()

    assert data["trip_id"] == seed["trip"].id
    assert data["start_date"] == "2024-06-01"
    assert data["end_date"] == "2024-06-10"
    assert len(data["photos"]) == 1

    photo = data["photos"][0]
    assert photo["ig_id"] == "IG_100"
    assert photo["media_id"] == seed["media"].id
    assert photo["caption"] == "Test caption"
    assert photo["is_aerial"] is False
    assert photo["permalink"] == "https://instagram.com/p/IG_100"


def test_trip_photos_excludes_video(client: TestClient, db_session: "Session") -> None:
    """Trip photos endpoint excludes VIDEO media."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_MIX",
        media_type="CAROUSEL_ALBUM",
    )
    _make_media(db_session, post, media_order=0, media_type="IMAGE", ig_media_id="I1")
    _make_media(db_session, post, media_order=1, media_type="VIDEO", ig_media_id="V1")
    _make_media(db_session, post, media_order=2, media_type="IMAGE", ig_media_id="I2")

    response = client.get(f"/api/v1/travels/photos/{trip.id}")
    data = response.json()
    assert len(data["photos"]) == 2


def test_trip_photos_ordered_by_posted_at_desc(
    client: TestClient, db_session: "Session"
) -> None:
    """Trip photos are ordered by posted_at descending (most recent first)."""
    from datetime import datetime

    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    early = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_EARLY",
        posted_at=datetime(2024, 6, 2, 10, 0, 0),
    )
    _make_media(db_session, early)

    late = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_LATE",
        posted_at=datetime(2024, 6, 8, 10, 0, 0),
    )
    _make_media(db_session, late)

    response = client.get(f"/api/v1/travels/photos/{trip.id}")
    data = response.json()
    assert len(data["photos"]) == 2
    # Most recent first
    assert data["photos"][0]["ig_id"] == "IG_LATE"
    assert data["photos"][1]["ig_id"] == "IG_EARLY"


def test_trip_photos_includes_destinations(
    client: TestClient, db_session: "Session"
) -> None:
    """Trip photos response includes destination names."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country, name="Prague")
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_DEST",
    )
    _make_media(db_session, post)

    response = client.get(f"/api/v1/travels/photos/{trip.id}")
    data = response.json()
    assert "Prague" in data["destinations"]


def test_trip_photos_empty_trip(client: TestClient, db_session: "Session") -> None:
    """Trip with no labeled photos returns empty photos list."""
    trip = _make_trip(db_session)

    response = client.get(f"/api/v1/travels/photos/{trip.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == trip.id
    assert data["photos"] == []


# ---------------------------------------------------------------------------
# 3. Photo map
# ---------------------------------------------------------------------------


def test_photo_map_with_data(client: TestClient, db_session: "Session") -> None:
    """Photo map returns countries with photo counts and thumbnails."""
    seed = _seed_full_photo_set(db_session)

    response = client.get("/api/v1/travels/photos/map")
    assert response.status_code == 200
    data = response.json()

    assert data["total_photos"] == 1
    assert len(data["countries"]) == 1

    c = data["countries"][0]
    assert c["un_country_id"] == seed["country"].id
    assert c["country_name"] == "Testland"
    assert c["iso_alpha2"] == "TL"
    assert c["iso_numeric"] == "999"
    assert c["photo_count"] == 1
    assert c["thumbnail_media_id"] == seed["media"].id
    assert c["latitude"] == 50.0
    assert c["longitude"] == 10.0


def test_photo_map_multiple_countries(
    client: TestClient, db_session: "Session"
) -> None:
    """Photo map aggregates counts per country."""
    country_a = _make_country(
        db_session,
        name="Alpha",
        iso_alpha2="AA",
        iso_alpha3="AAA",
        iso_numeric="101",
        capital_lat=40.0,
        capital_lng=20.0,
    )
    country_b = _make_country(
        db_session,
        name="Beta",
        iso_alpha2="BB",
        iso_alpha3="BBB",
        iso_numeric="102",
        capital_lat=30.0,
        capital_lng=15.0,
    )
    tcc_a = _make_tcc_destination(db_session, country_a, tcc_index=200, name="Alpha City")
    tcc_b = _make_tcc_destination(db_session, country_b, tcc_index=201, name="Beta City")

    trip = _make_trip(db_session)

    post_a = _make_post(
        db_session, trip=trip, tcc_dest=tcc_a, country=country_a, ig_id="IG_A"
    )
    _make_media(db_session, post_a)

    post_b = _make_post(
        db_session, trip=trip, tcc_dest=tcc_b, country=country_b, ig_id="IG_B"
    )
    _make_media(db_session, post_b)

    response = client.get("/api/v1/travels/photos/map")
    data = response.json()

    assert data["total_photos"] == 2
    assert len(data["countries"]) == 2
    names = {c["country_name"] for c in data["countries"]}
    assert names == {"Alpha", "Beta"}


def test_photo_map_excludes_video_media(
    client: TestClient, db_session: "Session"
) -> None:
    """Photo map counts exclude VIDEO media."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)

    post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_MAP_VID",
        media_type="CAROUSEL_ALBUM",
    )
    _make_media(db_session, post, media_order=0, media_type="IMAGE", ig_media_id="MI1")
    _make_media(db_session, post, media_order=1, media_type="VIDEO", ig_media_id="MV1")

    response = client.get("/api/v1/travels/photos/map")
    data = response.json()
    assert data["total_photos"] == 1


def test_photo_map_excludes_country_without_coords(
    client: TestClient, db_session: "Session"
) -> None:
    """Countries without capital_lat/capital_lng are omitted from map."""
    country = _make_country(db_session, capital_lat=None, capital_lng=None)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)

    post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_NOCOORD",
    )
    _make_media(db_session, post)

    response = client.get("/api/v1/travels/photos/map")
    data = response.json()
    assert data["total_photos"] == 0
    assert len(data["countries"]) == 0


# ---------------------------------------------------------------------------
# 4. Country photos
# ---------------------------------------------------------------------------


def test_country_photos_with_data(client: TestClient, db_session: "Session") -> None:
    """Country photos returns photos grouped by trip."""
    seed = _seed_full_photo_set(db_session)

    response = client.get(
        f"/api/v1/travels/photos/country/{seed['country'].id}"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["un_country_id"] == seed["country"].id
    assert data["country_name"] == "Testland"
    assert data["iso_alpha2"] == "TL"
    assert data["photo_count"] == 1
    assert len(data["trips"]) == 1

    trip_group = data["trips"][0]
    assert trip_group["trip_id"] == seed["trip"].id
    assert len(trip_group["photos"]) == 1
    assert trip_group["photos"][0]["ig_id"] == "IG_100"
    assert trip_group["photos"][0]["media_id"] == seed["media"].id


def test_country_photos_multiple_trips(
    client: TestClient, db_session: "Session"
) -> None:
    """Country photos groups photos by trip, sorted by start_date desc."""
    from datetime import date, datetime

    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)

    trip_old = _make_trip(
        db_session, start_date=date(2023, 1, 1), end_date=date(2023, 1, 10)
    )
    trip_new = _make_trip(
        db_session, start_date=date(2024, 6, 1), end_date=date(2024, 6, 10)
    )
    _link_trip_destination(db_session, trip_old, tcc_dest)
    _link_trip_destination(db_session, trip_new, tcc_dest)

    post_old = _make_post(
        db_session,
        trip=trip_old,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_OLD",
        posted_at=datetime(2023, 1, 5, 12, 0, 0),
    )
    _make_media(db_session, post_old)

    post_new = _make_post(
        db_session,
        trip=trip_new,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_NEW",
        posted_at=datetime(2024, 6, 5, 12, 0, 0),
    )
    _make_media(db_session, post_new)

    response = client.get(f"/api/v1/travels/photos/country/{country.id}")
    data = response.json()

    assert data["photo_count"] == 2
    assert len(data["trips"]) == 2
    # Most recent trip first
    assert data["trips"][0]["trip_id"] == trip_new.id
    assert data["trips"][1]["trip_id"] == trip_old.id


def test_country_photos_excludes_video(
    client: TestClient, db_session: "Session"
) -> None:
    """Country photos endpoint excludes VIDEO media."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_CVID",
        media_type="CAROUSEL_ALBUM",
    )
    _make_media(db_session, post, media_order=0, media_type="IMAGE", ig_media_id="CI1")
    _make_media(db_session, post, media_order=1, media_type="VIDEO", ig_media_id="CV1")

    response = client.get(f"/api/v1/travels/photos/country/{country.id}")
    data = response.json()
    assert data["photo_count"] == 1


def test_country_photos_no_tcc_destinations(
    client: TestClient, db_session: "Session"
) -> None:
    """Country with no TCC destinations returns empty trips list."""
    country = _make_country(db_session)

    response = client.get(f"/api/v1/travels/photos/country/{country.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["photo_count"] == 0
    assert data["trips"] == []


# ---------------------------------------------------------------------------
# 5. Set cover photo (admin only)
# ---------------------------------------------------------------------------


def test_set_cover_photo(admin_client: TestClient, db_session: "Session") -> None:
    """Admin can set a cover photo for a trip."""
    seed = _seed_full_photo_set(db_session)

    response = admin_client.post(
        f"/api/v1/travels/photos/{seed['trip'].id}/cover/{seed['media'].id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["trip_id"] == seed["trip"].id
    assert data["media_id"] == seed["media"].id

    # Verify the post is now marked as cover
    db_session.refresh(seed["post"])
    assert seed["post"].is_cover is True
    assert seed["post"].cover_media_id == seed["media"].id


def test_set_cover_clears_previous_cover(
    admin_client: TestClient, db_session: "Session"
) -> None:
    """Setting a new cover clears the previous cover in the same trip."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    post1 = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_COV1",
        is_cover=True,
    )
    media1 = _make_media(db_session, post1, ig_media_id="M_COV1")

    post2 = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_COV2",
    )
    media2 = _make_media(db_session, post2, ig_media_id="M_COV2")

    # Set post2 as cover
    response = admin_client.post(
        f"/api/v1/travels/photos/{trip.id}/cover/{media2.id}"
    )
    assert response.status_code == 200

    db_session.refresh(post1)
    db_session.refresh(post2)
    assert post1.is_cover is False
    assert post1.cover_media_id is None
    assert post2.is_cover is True
    assert post2.cover_media_id == media2.id


def test_set_cover_requires_auth(client: TestClient, db_session: "Session") -> None:
    """Set cover endpoint returns 401 without admin auth."""
    seed = _seed_full_photo_set(db_session)

    response = client.post(
        f"/api/v1/travels/photos/{seed['trip'].id}/cover/{seed['media'].id}"
    )
    assert response.status_code == 401


def test_set_cover_media_not_in_trip(
    admin_client: TestClient, db_session: "Session"
) -> None:
    """Setting cover with media from a different trip returns 404."""
    from datetime import date

    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)

    trip1 = _make_trip(db_session, start_date=date(2024, 1, 1), end_date=date(2024, 1, 10))
    trip2 = _make_trip(db_session, start_date=date(2024, 6, 1), end_date=date(2024, 6, 10))
    _link_trip_destination(db_session, trip1, tcc_dest)
    _link_trip_destination(db_session, trip2, tcc_dest)

    post = _make_post(
        db_session, trip=trip1, tcc_dest=tcc_dest, country=country, ig_id="IG_T1"
    )
    media = _make_media(db_session, post)

    # Try to set as cover on trip2 -- media belongs to trip1
    response = admin_client.post(
        f"/api/v1/travels/photos/{trip2.id}/cover/{media.id}"
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 6. Toggle hidden (admin only)
# ---------------------------------------------------------------------------


def test_toggle_hidden_hides_trip(
    admin_client: TestClient, db_session: "Session"
) -> None:
    """Toggle hidden on a visible trip hides it."""
    trip = _make_trip(db_session)

    response = admin_client.post(
        f"/api/v1/travels/photos/{trip.id}/toggle-hidden"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["trip_id"] == trip.id
    assert data["is_hidden"] is True

    db_session.refresh(trip)
    assert trip.hidden_from_photos is True


def test_toggle_hidden_unhides_trip(
    admin_client: TestClient, db_session: "Session"
) -> None:
    """Toggle hidden on a hidden trip unhides it."""
    trip = _make_trip(db_session, hidden_from_photos=True)

    response = admin_client.post(
        f"/api/v1/travels/photos/{trip.id}/toggle-hidden"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_hidden"] is False

    db_session.refresh(trip)
    assert trip.hidden_from_photos is False


def test_toggle_hidden_requires_auth(
    client: TestClient, db_session: "Session"
) -> None:
    """Toggle hidden endpoint returns 401 without admin auth."""
    trip = _make_trip(db_session)

    response = client.post(
        f"/api/v1/travels/photos/{trip.id}/toggle-hidden"
    )
    assert response.status_code == 401


def test_toggle_hidden_nonexistent_trip(
    admin_client: TestClient,
) -> None:
    """Toggle hidden on a nonexistent trip returns 404."""
    response = admin_client.post(
        "/api/v1/travels/photos/99999/toggle-hidden"
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 7. Hidden trips excluded from public endpoints
# ---------------------------------------------------------------------------


def test_hidden_trip_excluded_from_index(
    client: TestClient, db_session: "Session"
) -> None:
    """Hidden trips are excluded from the public photos index."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session, hidden_from_photos=True)
    _link_trip_destination(db_session, trip, tcc_dest)

    post = _make_post(
        db_session, trip=trip, tcc_dest=tcc_dest, country=country, ig_id="IG_HIDDEN"
    )
    _make_media(db_session, post)

    response = client.get("/api/v1/travels/photos")
    data = response.json()
    assert data["total_photos"] == 0
    assert data["total_trips"] == 0


def test_hidden_trip_visible_with_show_hidden(
    client: TestClient, db_session: "Session"
) -> None:
    """Hidden trips appear when show_hidden=true is passed."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session, hidden_from_photos=True)
    _link_trip_destination(db_session, trip, tcc_dest)

    post = _make_post(
        db_session, trip=trip, tcc_dest=tcc_dest, country=country, ig_id="IG_SH"
    )
    _make_media(db_session, post)

    response = client.get("/api/v1/travels/photos?show_hidden=true")
    data = response.json()
    assert data["total_trips"] == 1
    assert data["total_photos"] == 1
    assert data["years"][0]["trips"][0]["is_hidden"] is True


def test_mix_hidden_and_visible_trips(
    client: TestClient, db_session: "Session"
) -> None:
    """Only visible trips appear in the default index; hidden ones are excluded."""
    from datetime import date

    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)

    visible_trip = _make_trip(
        db_session, start_date=date(2024, 5, 1), end_date=date(2024, 5, 10)
    )
    hidden_trip = _make_trip(
        db_session,
        start_date=date(2024, 7, 1),
        end_date=date(2024, 7, 10),
        hidden_from_photos=True,
    )
    _link_trip_destination(db_session, visible_trip, tcc_dest)
    _link_trip_destination(db_session, hidden_trip, tcc_dest)

    post_vis = _make_post(
        db_session,
        trip=visible_trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_VIS",
    )
    _make_media(db_session, post_vis)

    post_hid = _make_post(
        db_session,
        trip=hidden_trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_HID",
    )
    _make_media(db_session, post_hid)

    # Default: only visible
    response = client.get("/api/v1/travels/photos")
    data = response.json()
    assert data["total_trips"] == 1
    assert data["years"][0]["trips"][0]["trip_id"] == visible_trip.id

    # With show_hidden: both
    response_all = client.get("/api/v1/travels/photos?show_hidden=true")
    data_all = response_all.json()
    assert data_all["total_trips"] == 2


# ---------------------------------------------------------------------------
# Edge cases and cover photo thumbnail selection
# ---------------------------------------------------------------------------


def test_cover_photo_used_as_thumbnail(
    client: TestClient, db_session: "Session"
) -> None:
    """When a post is marked as cover, its media is used as the trip thumbnail."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    # Regular post (not cover)
    regular_post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_REG",
        is_cover=False,
    )
    _make_media(db_session, regular_post, ig_media_id="M_REG")

    # Cover post
    cover_post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_COVER",
        is_cover=True,
    )
    cover_media = _make_media(db_session, cover_post, ig_media_id="M_COVER")

    response = client.get("/api/v1/travels/photos")
    data = response.json()
    assert data["total_trips"] == 1
    # Thumbnail should be from the cover post
    assert data["years"][0]["trips"][0]["thumbnail_media_id"] == cover_media.id


def test_set_cover_with_specific_media_id(
    admin_client: TestClient, db_session: "Session"
) -> None:
    """Admin can set a specific media item (carousel slide) as cover."""
    country = _make_country(db_session)
    tcc_dest = _make_tcc_destination(db_session, country)
    trip = _make_trip(db_session)
    _link_trip_destination(db_session, trip, tcc_dest)

    post = _make_post(
        db_session,
        trip=trip,
        tcc_dest=tcc_dest,
        country=country,
        ig_id="IG_CAROUSEL",
        media_type="CAROUSEL_ALBUM",
    )
    media1 = _make_media(db_session, post, media_order=0, ig_media_id="SLIDE_1")
    media2 = _make_media(db_session, post, media_order=1, ig_media_id="SLIDE_2")

    # Set second slide as cover
    response = admin_client.post(
        f"/api/v1/travels/photos/{trip.id}/cover/{media2.id}"
    )
    assert response.status_code == 200
    assert response.json()["media_id"] == media2.id

    db_session.refresh(post)
    assert post.is_cover is True
    assert post.cover_media_id == media2.id
