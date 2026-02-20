"""Tests for Instagram post labeling endpoints.

Covers CRUD operations, labeling transitions, stats, and navigation.
External API endpoints (fetch, sync, fill-gaps) are excluded — they
require mocked HTTP and are better tested via integration tests.
"""

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.session import get_admin_user
from src.database import Base, get_db
from src.main import app
from src.models import InstagramMedia, InstagramPost, User


@pytest.fixture()
def ig_admin(db_session: Session) -> User:
    """Create admin user for instagram tests."""
    user = User(
        email="igadmin@test.com",
        name="IG Admin",
        nickname="igadmin",
        is_admin=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def ig_client(db_session: Session, ig_admin: User) -> Generator[TestClient, None, None]:
    """Test client with admin auth for instagram endpoints."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_admin_user() -> User:
        return ig_admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_admin_user] = override_get_admin_user
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


def _create_post(
    db: Session,
    ig_id: str,
    posted_at: datetime,
    media_type: str = "IMAGE",
    labeled_at: datetime | None = None,
    skipped: bool = False,
    un_country_id: int | None = None,
    trip_id: int | None = None,
    is_cover: bool = False,
) -> InstagramPost:
    """Helper to create an InstagramPost with one media item."""
    post = InstagramPost(
        ig_id=ig_id,
        caption=f"Caption for {ig_id}",
        media_type=media_type,
        posted_at=posted_at,
        permalink=f"https://instagram.com/p/{ig_id}",
        fetched_at=datetime.now(UTC),
        labeled_at=labeled_at,
        skipped=skipped,
        un_country_id=un_country_id,
        trip_id=trip_id,
        is_cover=is_cover,
    )
    db.add(post)
    db.flush()

    media = InstagramMedia(
        post_id=post.id,
        ig_media_id=f"{ig_id}_media",
        media_order=0,
        media_type=media_type,
        storage_path=f"/data/{ig_id}.jpg" if media_type != "VIDEO" else None,
    )
    db.add(media)
    db.commit()
    db.refresh(post)
    return post


# --- Stats ---


def test_stats_empty(ig_client: TestClient) -> None:
    """Stats with no posts returns all zeros."""
    r = ig_client.get("/api/v1/admin/instagram/stats")
    assert r.status_code == 200
    data = r.json()
    assert data == {"total": 0, "labeled": 0, "skipped": 0, "unlabeled": 0}


def test_stats_counts(ig_client: TestClient, db_session: Session) -> None:
    """Stats correctly counts labeled, skipped, and unlabeled posts."""
    now = datetime(2025, 6, 1, tzinfo=UTC)
    _create_post(db_session, "post1", now, labeled_at=now)
    _create_post(db_session, "post2", now, labeled_at=now)
    _create_post(db_session, "post3", now, skipped=True)
    _create_post(db_session, "post4", now)  # unlabeled
    _create_post(db_session, "vid1", now, media_type="VIDEO")  # excluded

    r = ig_client.get("/api/v1/admin/instagram/stats")
    data = r.json()
    assert data["total"] == 4  # VIDEO excluded
    assert data["labeled"] == 2
    assert data["skipped"] == 1
    assert data["unlabeled"] == 1


# --- Post retrieval ---


def test_get_post_by_ig_id(ig_client: TestClient, db_session: Session) -> None:
    """Get a specific post by its Instagram ID."""
    now = datetime(2025, 6, 1, tzinfo=UTC)
    _create_post(db_session, "abc123", now)

    r = ig_client.get("/api/v1/admin/instagram/posts/abc123")
    assert r.status_code == 200
    data = r.json()
    assert data["ig_id"] == "abc123"
    assert data["caption"] == "Caption for abc123"
    assert len(data["media"]) == 1


def test_get_post_not_found(ig_client: TestClient) -> None:
    """404 for non-existent post."""
    r = ig_client.get("/api/v1/admin/instagram/posts/nonexistent")
    assert r.status_code == 404


def test_get_latest_post(ig_client: TestClient, db_session: Session) -> None:
    """Latest post returns the newest non-VIDEO post."""
    _create_post(db_session, "old", datetime(2025, 1, 1, tzinfo=UTC))
    _create_post(db_session, "new", datetime(2025, 6, 1, tzinfo=UTC))
    _create_post(db_session, "vid", datetime(2025, 12, 1, tzinfo=UTC), media_type="VIDEO")

    r = ig_client.get("/api/v1/admin/instagram/posts/latest")
    assert r.status_code == 200
    assert r.json() == "new"


def test_get_latest_post_empty(ig_client: TestClient) -> None:
    """Latest post returns null when no posts exist."""
    r = ig_client.get("/api/v1/admin/instagram/posts/latest")
    assert r.status_code == 200
    assert r.json() is None


# --- Unprocessed / skipped ---


def test_first_unprocessed(ig_client: TestClient, db_session: Session) -> None:
    """First unprocessed returns newest unlabeled, unskipped post."""
    _create_post(db_session, "labeled", datetime(2025, 6, 1, tzinfo=UTC), labeled_at=datetime.now(UTC))
    _create_post(db_session, "skipped", datetime(2025, 5, 1, tzinfo=UTC), skipped=True)
    _create_post(db_session, "unproc1", datetime(2025, 3, 1, tzinfo=UTC))
    _create_post(db_session, "unproc2", datetime(2025, 4, 1, tzinfo=UTC))

    r = ig_client.get("/api/v1/admin/instagram/posts/first-unprocessed")
    assert r.status_code == 200
    assert r.json() == "unproc2"  # newest of the two unprocessed


def test_first_unprocessed_none(ig_client: TestClient, db_session: Session) -> None:
    """Returns null when all posts are labeled or skipped."""
    now = datetime(2025, 6, 1, tzinfo=UTC)
    _create_post(db_session, "labeled", now, labeled_at=now)
    _create_post(db_session, "skipped", now, skipped=True)

    r = ig_client.get("/api/v1/admin/instagram/posts/first-unprocessed")
    assert r.json() is None


def test_first_skipped(ig_client: TestClient, db_session: Session) -> None:
    """First skipped returns the oldest skipped post."""
    _create_post(db_session, "skip_new", datetime(2025, 6, 1, tzinfo=UTC), skipped=True)
    _create_post(db_session, "skip_old", datetime(2025, 1, 1, tzinfo=UTC), skipped=True)
    _create_post(db_session, "normal", datetime(2025, 3, 1, tzinfo=UTC))

    r = ig_client.get("/api/v1/admin/instagram/posts/first-skipped")
    assert r.json() == "skip_old"


# --- Navigation ---


def test_navigation(ig_client: TestClient, db_session: Session) -> None:
    """Navigation returns prev (newer) and next (older) posts."""
    _create_post(db_session, "oldest", datetime(2025, 1, 1, tzinfo=UTC))
    _create_post(db_session, "middle", datetime(2025, 6, 1, tzinfo=UTC))
    _create_post(db_session, "newest", datetime(2025, 12, 1, tzinfo=UTC))

    r = ig_client.get("/api/v1/admin/instagram/posts/middle/nav")
    assert r.status_code == 200
    data = r.json()
    assert data["prev_ig_id"] == "newest"
    assert data["next_ig_id"] == "oldest"


def test_navigation_edges(ig_client: TestClient, db_session: Session) -> None:
    """First and last posts have null prev/next respectively."""
    _create_post(db_session, "only", datetime(2025, 6, 1, tzinfo=UTC))

    r = ig_client.get("/api/v1/admin/instagram/posts/only/nav")
    data = r.json()
    assert data["prev_ig_id"] is None
    assert data["next_ig_id"] is None


def test_navigation_not_found(ig_client: TestClient) -> None:
    """Navigation for non-existent post returns 404."""
    r = ig_client.get("/api/v1/admin/instagram/posts/ghost/nav")
    assert r.status_code == 404


# --- Labeling ---


def test_label_post(ig_client: TestClient, db_session: Session) -> None:
    """Labeling a post sets fields and labeled_at timestamp."""
    now = datetime(2025, 6, 1, tzinfo=UTC)
    _create_post(db_session, "to_label", now)

    r = ig_client.post(
        "/api/v1/admin/instagram/posts/to_label/label",
        json={"un_country_id": 42, "is_aerial": True},
    )
    assert r.status_code == 200
    assert r.json()["success"] is True

    # Verify in DB
    post = db_session.query(InstagramPost).filter(InstagramPost.ig_id == "to_label").first()
    assert post is not None
    assert post.un_country_id == 42
    assert post.is_aerial is True
    assert post.labeled_at is not None
    assert post.skipped is False


def test_skip_post(ig_client: TestClient, db_session: Session) -> None:
    """Skipping a post sets skipped=True and clears labeled_at."""
    now = datetime(2025, 6, 1, tzinfo=UTC)
    _create_post(db_session, "to_skip", now, labeled_at=now, un_country_id=1)

    r = ig_client.post(
        "/api/v1/admin/instagram/posts/to_skip/label",
        json={"skip": True},
    )
    assert r.status_code == 200

    post = db_session.query(InstagramPost).filter(InstagramPost.ig_id == "to_skip").first()
    assert post is not None
    assert post.skipped is True
    assert post.labeled_at is None


def test_label_clears_skipped(ig_client: TestClient, db_session: Session) -> None:
    """Labeling a previously-skipped post clears skipped flag."""
    now = datetime(2025, 6, 1, tzinfo=UTC)
    _create_post(db_session, "was_skipped", now, skipped=True)

    r = ig_client.post(
        "/api/v1/admin/instagram/posts/was_skipped/label",
        json={"un_country_id": 10},
    )
    assert r.status_code == 200

    post = db_session.query(InstagramPost).filter(InstagramPost.ig_id == "was_skipped").first()
    assert post is not None
    assert post.skipped is False
    assert post.labeled_at is not None
    assert post.un_country_id == 10


def test_label_not_found(ig_client: TestClient) -> None:
    """Labeling non-existent post returns 404."""
    r = ig_client.post(
        "/api/v1/admin/instagram/posts/ghost/label",
        json={"un_country_id": 1},
    )
    assert r.status_code == 404


def test_cover_replaces_previous(ig_client: TestClient, db_session: Session) -> None:
    """Setting a cover photo clears the previous cover in the same trip."""
    now = datetime(2025, 6, 1, tzinfo=UTC)
    old_cover = _create_post(db_session, "old_cover", now, labeled_at=now, trip_id=1, is_cover=True)
    _create_post(db_session, "new_cover", now)

    r = ig_client.post(
        "/api/v1/admin/instagram/posts/new_cover/label",
        json={"trip_id": 1, "is_cover": True, "cover_media_id": 99},
    )
    assert r.status_code == 200

    db_session.refresh(old_cover)
    assert old_cover.is_cover is False
    assert old_cover.cover_media_id is None

    new = db_session.query(InstagramPost).filter(InstagramPost.ig_id == "new_cover").first()
    assert new is not None
    assert new.is_cover is True
    assert new.cover_media_id == 99


# --- Auth ---


def test_requires_admin(client: TestClient) -> None:
    """Instagram endpoints require admin auth."""
    r = client.get("/api/v1/admin/instagram/stats")
    assert r.status_code == 401
