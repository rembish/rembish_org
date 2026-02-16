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
