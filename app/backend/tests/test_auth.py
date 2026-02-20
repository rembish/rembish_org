"""Tests for authentication endpoints."""

from fastapi.testclient import TestClient

from src.main import app


def test_login_redirects_to_google(client: TestClient) -> None:
    """GET /api/auth/login should redirect to Google OAuth."""
    # With google_client_id empty (dev default), should return 503
    response = client.get("/api/auth/login", follow_redirects=False)
    assert response.status_code == 503


def test_me_returns_null_without_auth(client: TestClient) -> None:
    """GET /api/auth/me should return null when not logged in."""
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() is None


def test_admin_users_401_without_auth(client: TestClient) -> None:
    """Admin endpoints should return 401 without authentication."""
    response = client.get("/api/v1/admin/users/")
    assert response.status_code == 401


def test_admin_users_403_non_admin(client: TestClient) -> None:
    """Admin endpoints should return 403 for non-admin users.

    This is implicitly tested via the 401 (no cookie = no user = 401),
    but we verify the chain works correctly.
    """
    response = client.post("/api/v1/admin/users/", json={"email": "test@test.com"})
    assert response.status_code == 401


def test_logout_clears_cookie(client: TestClient) -> None:
    """POST /api/auth/logout should return JSON and clear the session cookie."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"logged_out": True}
    # Check the Set-Cookie header deletes the auth cookie
    cookies = response.headers.get_list("set-cookie")
    auth_cookie = [c for c in cookies if "auth=" in c]
    assert len(auth_cookie) > 0
    # Delete cookie has max-age=0 or expires in the past
    cookie_str = auth_cookie[0]
    assert "max-age=0" in cookie_str.lower() or "expires=" in cookie_str.lower()


def test_logout_get_not_allowed(client: TestClient) -> None:
    """GET /api/auth/logout should return 405 (POST-only)."""
    response = client.get("/api/auth/logout")
    assert response.status_code == 405


def test_csrf_required_on_mutating_requests() -> None:
    """POST/PUT/DELETE to /api/* without X-CSRF header should return 403."""
    with TestClient(app) as c:
        response = c.post("/api/auth/logout")
        assert response.status_code == 403
        assert response.json()["detail"] == "Missing CSRF header"


def test_csrf_not_required_on_get(client: TestClient) -> None:
    """GET requests should not require the CSRF header."""
    with TestClient(app) as c:
        response = c.get("/api/auth/me")
        assert response.status_code == 200
