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
