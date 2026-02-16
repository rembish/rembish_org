"""Tests for health and info endpoints."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_info_returns_version(client: TestClient) -> None:
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "rembish.org"
    assert "version" in data
    # Version should be a semver-like string
    parts = data["version"].split(".")
    assert len(parts) == 3
