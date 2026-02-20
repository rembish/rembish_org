"""Tests for app middleware (security headers, CSRF) and root endpoints."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database import get_db
from src.main import app


@pytest.fixture()
def bare_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Test client WITHOUT X-CSRF header — for CSRF middleware tests."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


def test_security_header_content_type_options(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_security_header_frame_options(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_header_referrer_policy(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_security_header_permissions_policy(client: TestClient) -> None:
    response = client.get("/health")
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_security_header_xss_protection(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


# ---------------------------------------------------------------------------
# CSRF middleware
# ---------------------------------------------------------------------------


def test_csrf_blocks_post_to_api_without_header(bare_client: TestClient) -> None:
    """POST to /api/* without X-CSRF header should return 403."""
    response = bare_client.post("/api/auth/logout")
    assert response.status_code == 403
    assert response.json()["detail"] == "Missing CSRF header"


def test_csrf_allows_post_to_api_with_header(client: TestClient) -> None:
    """POST to /api/* WITH X-CSRF header should pass through (client fixture has it)."""
    response = client.post("/api/auth/logout")
    # Should not be 403 — the request passes CSRF and reaches the endpoint
    assert response.status_code != 403


def test_csrf_allows_get_without_header(bare_client: TestClient) -> None:
    """GET requests should never be blocked by CSRF middleware."""
    response = bare_client.get("/api/v1/info")
    assert response.status_code == 200


def test_csrf_does_not_apply_to_non_api_paths(bare_client: TestClient) -> None:
    """Non-/api/ paths should not be subject to CSRF checks."""
    response = bare_client.get("/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Root endpoints
# ---------------------------------------------------------------------------


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_info_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "rembish.org"
    parts = data["version"].split(".")
    assert len(parts) == 3
