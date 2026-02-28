"""Tests for Bearer token authentication and CSRF exemption."""

from collections.abc import Generator
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database import get_db
from src.main import app
from src.models import User


def _create_admin(db: Session) -> User:
    user = User(
        email="admin@test.com",
        name="Test Admin",
        nickname="admin",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _bearer_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Client with DB override only (no auth override, no CSRF header)."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_valid_bearer_token(db_session: Session) -> None:
    """Valid bearer token authenticates as admin."""
    admin = _create_admin(db_session)
    with patch("src.auth.session.settings") as mock_settings:
        mock_settings.app_token = "test-secret-token"
        mock_settings.secret_key = "dev-secret-change-in-production"
        for client in _bearer_client(db_session):
            resp = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer test-secret-token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data is not None
            assert data["email"] == admin.email
            assert data["role"] == "admin"


def test_wrong_bearer_token(db_session: Session) -> None:
    """Wrong bearer token does not authenticate."""
    _create_admin(db_session)
    with patch("src.auth.session.settings") as mock_settings:
        mock_settings.app_token = "test-secret-token"
        mock_settings.secret_key = "dev-secret-change-in-production"
        for client in _bearer_client(db_session):
            resp = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer wrong-token"},
            )
            assert resp.status_code == 200
            assert resp.json() is None


def test_empty_app_token_disables_bearer(db_session: Session) -> None:
    """Empty app_token config disables bearer auth entirely."""
    _create_admin(db_session)
    with patch("src.auth.session.settings") as mock_settings:
        mock_settings.app_token = ""
        mock_settings.secret_key = "dev-secret-change-in-production"
        for client in _bearer_client(db_session):
            resp = client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer any-token"},
            )
            assert resp.status_code == 200
            assert resp.json() is None


def test_bearer_skips_csrf(db_session: Session) -> None:
    """Bearer request to mutating endpoint does not require X-CSRF header."""
    _create_admin(db_session)
    with patch("src.auth.session.settings") as mock_settings:
        mock_settings.app_token = "test-secret-token"
        mock_settings.secret_key = "dev-secret-change-in-production"
        for client in _bearer_client(db_session):
            # POST without X-CSRF but with Bearer — should not get 403 CSRF error
            resp = client.post(
                "/api/auth/logout",
                headers={"Authorization": "Bearer test-secret-token"},
            )
            assert resp.status_code == 200


def test_no_bearer_no_csrf_still_blocked(db_session: Session) -> None:
    """Without bearer and without CSRF, mutating requests are blocked."""
    for client in _bearer_client(db_session):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]


def test_cookie_takes_priority(db_session: Session) -> None:
    """When both cookie and bearer are present, cookie auth is used."""
    admin = _create_admin(db_session)
    from src.auth.session import create_session_token

    token = create_session_token(admin.id)

    with patch("src.auth.session.settings") as mock_settings:
        mock_settings.app_token = "test-secret-token"
        mock_settings.secret_key = "dev-secret-change-in-production"
        for client in _bearer_client(db_session):
            client.cookies.set("auth", token)
            resp = client.get(
                "/api/auth/me",
                headers={
                    "Authorization": "Bearer test-secret-token",
                    "X-CSRF": "1",
                },
            )
            assert resp.status_code == 200
            assert resp.json() is not None
            assert resp.json()["email"] == admin.email
