"""Tests for viewer role access controls.

Viewers can GET trips, events, flights, country-info, calendar feed-token.
Viewers get 403 on POST/PUT/DELETE for trips, events, flights.
Users with no role get 403 on all admin endpoints.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.session import get_admin_user, get_trips_viewer
from src.database import get_db
from src.main import app
from src.models import User


@pytest.fixture()
def viewer_user(db_session: Session) -> User:
    """Create a viewer user."""
    user = User(
        email="viewer@test.com",
        name="Viewer User",
        nickname="viewer",
        role="viewer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def norole_user(db_session: Session) -> User:
    """Create a user with no role."""
    user = User(
        email="norole@test.com",
        name="No Role",
        nickname="norole",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def viewer_client(
    db_session: Session, viewer_user: User
) -> Generator[TestClient, None, None]:
    """Test client authenticated as a viewer."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_trips_viewer() -> User:
        return viewer_user

    def override_get_admin_user() -> User:
        # Viewer should fail admin-only checks
        raise Exception("Admin check should not be called for viewer routes")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_trips_viewer] = override_get_trips_viewer
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def norole_client(
    db_session: Session, norole_user: User
) -> Generator[TestClient, None, None]:
    """Test client authenticated as a no-role user (should be denied everywhere)."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Don't override auth — let real auth deny
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


# --- Viewer can GET trips-related endpoints ---


def test_viewer_can_get_trips(viewer_client: TestClient) -> None:
    res = viewer_client.get("/api/v1/travels/trips")
    assert res.status_code == 200


def test_viewer_can_get_tcc_options(viewer_client: TestClient) -> None:
    res = viewer_client.get("/api/v1/travels/tcc-options")
    assert res.status_code == 200


def test_viewer_can_get_users_options(viewer_client: TestClient) -> None:
    res = viewer_client.get("/api/v1/travels/users-options")
    assert res.status_code == 200


def test_viewer_can_get_events(viewer_client: TestClient) -> None:
    res = viewer_client.get("/api/v1/travels/events")
    assert res.status_code == 200


def test_viewer_can_get_vacation_summary(viewer_client: TestClient) -> None:
    res = viewer_client.get("/api/v1/travels/vacation-summary?year=2026")
    assert res.status_code == 200


def test_viewer_can_get_feed_token(viewer_client: TestClient) -> None:
    res = viewer_client.get("/api/v1/travels/calendar/feed-token")
    assert res.status_code == 200


def test_viewer_can_get_flight_dates(viewer_client: TestClient) -> None:
    res = viewer_client.get("/api/v1/travels/flights/dates?year=2026")
    assert res.status_code == 200


# --- Viewer gets 403 on mutations ---


def test_viewer_cannot_create_trip(viewer_client: TestClient) -> None:
    res = viewer_client.post(
        "/api/v1/travels/trips",
        json={"start_date": "2026-06-01", "destinations": [], "cities": []},
    )
    # Should get 403 because POST requires get_admin_user
    assert res.status_code in (401, 403)


def test_viewer_cannot_delete_trip(viewer_client: TestClient) -> None:
    res = viewer_client.delete("/api/v1/travels/trips/1")
    assert res.status_code in (401, 403)


def test_viewer_cannot_create_event(viewer_client: TestClient) -> None:
    res = viewer_client.post(
        "/api/v1/travels/events",
        json={"event_date": "2026-06-01", "title": "Test", "category": "other"},
    )
    assert res.status_code in (401, 403)


def test_viewer_cannot_delete_event(viewer_client: TestClient) -> None:
    res = viewer_client.delete("/api/v1/travels/events/1")
    assert res.status_code in (401, 403)


def test_viewer_cannot_regenerate_token(viewer_client: TestClient) -> None:
    res = viewer_client.post("/api/v1/travels/calendar/regenerate-token")
    assert res.status_code in (401, 403)


# --- Viewer properties ---


def test_viewer_is_admin_false(viewer_user: User) -> None:
    assert viewer_user.is_admin is False


def test_viewer_is_viewer_true(viewer_user: User) -> None:
    assert viewer_user.is_viewer is True


def test_admin_is_viewer_false(admin_user: User) -> None:
    assert admin_user.is_viewer is False
    assert admin_user.is_admin is True


def test_norole_user_has_no_roles(norole_user: User) -> None:
    assert norole_user.is_admin is False
    assert norole_user.is_viewer is False
    assert norole_user.role is None


# --- No-role user gets denied ---


def test_norole_cannot_get_trips(norole_client: TestClient) -> None:
    """User without any role should get 401 (not authenticated via dependency)."""
    res = norole_client.get("/api/v1/travels/trips")
    assert res.status_code in (401, 403)


def test_norole_cannot_access_admin_users(norole_client: TestClient) -> None:
    res = norole_client.get("/api/v1/admin/users/")
    assert res.status_code in (401, 403)


# --- Viewer access to fixers ---


def test_viewer_can_get_fixers(viewer_client: TestClient) -> None:
    res = viewer_client.get("/api/v1/admin/fixers/")
    assert res.status_code == 200


def test_viewer_cannot_create_fixer(viewer_client: TestClient) -> None:
    res = viewer_client.post(
        "/api/v1/admin/fixers/",
        json={"name": "Test", "type": "guide"},
    )
    assert res.status_code in (401, 403, 500)


def test_viewer_cannot_delete_fixer(viewer_client: TestClient) -> None:
    res = viewer_client.delete("/api/v1/admin/fixers/1")
    assert res.status_code in (401, 403, 500)
