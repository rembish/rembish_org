"""Extended auth tests: redirect validation, vault lock/status, session edge cases."""

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.routes import _validate_redirect
from src.auth.session import (
    SESSION_COOKIE_NAME,
    VAULT_COOKIE_NAME,
    create_session_token,
    create_vault_token,
    get_admin_user,
    get_current_user_optional,
    verify_session_token,
)
from src.database import get_db
from src.main import app
from src.models import User


# --- Redirect Validation ---


def test_validate_redirect_normal() -> None:
    assert _validate_redirect("/admin") == "/admin"
    assert _validate_redirect("/trips/42") == "/trips/42"


def test_validate_redirect_empty() -> None:
    assert _validate_redirect(None) == "/"
    assert _validate_redirect("") == "/"


def test_validate_redirect_open_redirect() -> None:
    """Rejects paths that could be open redirects."""
    assert _validate_redirect("//evil.com") == "/"
    assert _validate_redirect("https://evil.com") == "/"
    assert _validate_redirect("http://evil.com") == "/"


def test_validate_redirect_backslash() -> None:
    assert _validate_redirect("/path\\evil") == "/"


def test_validate_redirect_header_injection() -> None:
    assert _validate_redirect("/path\r\nHeader: evil") == "/"
    assert _validate_redirect("/path\nHeader: evil") == "/"


def test_validate_redirect_relative_path() -> None:
    """Non-absolute paths are rejected."""
    assert _validate_redirect("relative/path") == "/"


# --- Vault Lock ---


def test_vault_lock(client: TestClient) -> None:
    """POST /api/auth/vault/lock clears vault cookie."""
    res = client.post("/api/auth/vault/lock")
    assert res.status_code == 200
    assert res.json() == {"locked": True}

    cookies = res.headers.get_list("set-cookie")
    vault_cookie = [c for c in cookies if "vault_auth=" in c]
    assert len(vault_cookie) > 0


# --- Vault Status ---


def test_vault_status_unlocked(db_session: Session, admin_user: User) -> None:
    """Vault status returns unlocked when valid vault token is present."""
    vault_token = create_vault_token(admin_user.id)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_admin() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_admin_user] = override_get_admin
    app.dependency_overrides[get_current_user_optional] = lambda: admin_user

    with TestClient(
        app,
        headers={"X-CSRF": "1"},
        cookies={VAULT_COOKIE_NAME: vault_token},
    ) as c:
        res = c.get("/api/auth/vault/status")
    app.dependency_overrides.clear()

    assert res.status_code == 200
    assert res.json()["unlocked"] is True


def test_vault_status_locked_no_cookie(client: TestClient) -> None:
    """Vault status without cookie returns locked."""
    res = client.get("/api/auth/vault/status")
    assert res.status_code == 200
    assert res.json()["unlocked"] is False


def test_vault_status_locked_invalid_token(admin_client: TestClient) -> None:
    """Vault status with invalid token returns locked."""
    admin_client.cookies.set(VAULT_COOKIE_NAME, "invalid-token")
    res = admin_client.get("/api/auth/vault/status")
    assert res.status_code == 200
    assert res.json()["unlocked"] is False


def test_vault_status_locked_wrong_user(
    db_session: Session, admin_user: User
) -> None:
    """Vault status with token for different user returns locked."""
    # Create token for user ID 999 (doesn't match admin)
    wrong_token = create_vault_token(999)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_admin() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db

    # Need an authenticated client that also has wrong vault token
    # vault_status checks user from session vs user_id in vault token
    def override_get_user_optional() -> User:
        return admin_user

    app.dependency_overrides[get_current_user_optional] = override_get_user_optional

    with TestClient(app, headers={"X-CSRF": "1"}, cookies={VAULT_COOKIE_NAME: wrong_token}) as c:
        res = c.get("/api/auth/vault/status")
        assert res.status_code == 200
        assert res.json()["unlocked"] is False

    app.dependency_overrides.clear()


# --- Login without OAuth configured ---


def test_login_503_without_oauth(client: TestClient) -> None:
    """Login returns 503 when Google OAuth is not configured."""
    res = client.get("/api/auth/login", follow_redirects=False)
    assert res.status_code == 503


def test_vault_login_503_without_oauth(client: TestClient) -> None:
    """Vault login returns 503 when Google OAuth is not configured."""
    res = client.get("/api/auth/vault/login", follow_redirects=False)
    assert res.status_code == 503


# --- /me with authenticated user ---


def test_me_returns_user(db_session: Session, admin_user: User) -> None:
    """GET /api/auth/me returns user info when authenticated."""
    session_token = create_session_token(admin_user.id)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, cookies={SESSION_COOKIE_NAME: session_token}, headers={"X-CSRF": "1"}) as c:
        res = c.get("/api/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
        assert data["is_admin"] is True
    app.dependency_overrides.clear()


# --- Session with expired/invalid token ---


def test_me_returns_null_with_invalid_token(db_session: Session) -> None:
    """GET /api/auth/me with invalid token returns null."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, cookies={SESSION_COOKIE_NAME: "garbage"}, headers={"X-CSRF": "1"}) as c:
        res = c.get("/api/auth/me")
        assert res.status_code == 200
        assert res.json() is None
    app.dependency_overrides.clear()


def test_session_token_for_nonexistent_user(db_session: Session) -> None:
    """Session token for deleted user returns null from /me."""
    token = create_session_token(99999)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, cookies={SESSION_COOKIE_NAME: token}, headers={"X-CSRF": "1"}) as c:
        res = c.get("/api/auth/me")
        assert res.status_code == 200
        assert res.json() is None
    app.dependency_overrides.clear()
