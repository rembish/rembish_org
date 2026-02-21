"""Tests for admin user management endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import User


def test_list_users_excludes_admin(admin_client: TestClient) -> None:
    """List users should not include the current admin."""
    response = admin_client.get("/api/v1/admin/users/")
    assert response.status_code == 200
    data = response.json()
    assert data["users"] == []


def test_list_users_includes_others(admin_client: TestClient, db_session: Session) -> None:
    """List users should include non-admin users."""
    user = User(email="other@test.com", name="Other",is_active=True)
    db_session.add(user)
    db_session.commit()

    response = admin_client.get("/api/v1/admin/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 1
    assert data["users"][0]["email"] == "other@test.com"


def test_create_user(admin_client: TestClient) -> None:
    """Create a new user."""
    response = admin_client.post(
        "/api/v1/admin/users/",
        json={"email": "new@test.com", "name": "New User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@test.com"
    assert data["name"] == "New User"
    assert data["is_active"] is False  # Pending until first login
    assert data["role"] is None
    assert data["is_admin"] is False


def test_create_user_duplicate_email(admin_client: TestClient) -> None:
    """Duplicate email should return 409."""
    admin_client.post(
        "/api/v1/admin/users/",
        json={"email": "dup@test.com"},
    )
    response = admin_client.post(
        "/api/v1/admin/users/",
        json={"email": "dup@test.com"},
    )
    assert response.status_code == 409


def test_create_user_invalid_email(admin_client: TestClient) -> None:
    """Invalid email should return 422."""
    response = admin_client.post(
        "/api/v1/admin/users/",
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422


def test_update_user(admin_client: TestClient, db_session: Session) -> None:
    """Update an existing user."""
    user = User(email="update@test.com", name="Old Name", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = admin_client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"name": "New Name", "nickname": "nick"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["nickname"] == "nick"


def test_update_user_not_found(admin_client: TestClient) -> None:
    """Update non-existent user should return 404."""
    response = admin_client.put(
        "/api/v1/admin/users/99999",
        json={"name": "Test"},
    )
    assert response.status_code == 404


def test_self_edit_prevention(admin_client: TestClient, admin_user: User) -> None:
    """Admin should not be able to edit their own record."""
    response = admin_client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        json={"name": "Sneaky"},
    )
    assert response.status_code == 403


def test_delete_user(admin_client: TestClient, db_session: Session) -> None:
    """Delete an existing user."""
    user = User(email="delete@test.com", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = admin_client.delete(f"/api/v1/admin/users/{user.id}")
    assert response.status_code == 204

    # Verify deletion
    assert db_session.query(User).filter(User.id == user.id).first() is None


def test_self_delete_prevention(admin_client: TestClient, admin_user: User) -> None:
    """Admin should not be able to delete themselves."""
    response = admin_client.delete(f"/api/v1/admin/users/{admin_user.id}")
    assert response.status_code == 403


def test_delete_user_not_found(admin_client: TestClient) -> None:
    """Delete non-existent user should return 404."""
    response = admin_client.delete("/api/v1/admin/users/99999")
    assert response.status_code == 404


def test_update_user_role(admin_client: TestClient, db_session: Session) -> None:
    """Set a user's role to viewer."""
    user = User(email="role@test.com", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = admin_client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"role": "viewer"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "viewer"
    assert data["is_admin"] is False

    # Clear role by sending empty string
    response = admin_client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"role": ""},
    )
    assert response.status_code == 200
    assert response.json()["role"] is None


def test_update_user_invalid_role(admin_client: TestClient, db_session: Session) -> None:
    """Invalid role value should return 422."""
    user = User(email="badrole@test.com", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = admin_client.put(
        f"/api/v1/admin/users/{user.id}",
        json={"role": "superadmin"},
    )
    assert response.status_code == 422
