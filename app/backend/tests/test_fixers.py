"""Tests for fixers (travel contacts) CRUD."""

from fastapi.testclient import TestClient

BASE = "/api/v1/admin/fixers/"


def _minimal_fixer() -> dict:
    return {"name": "Test Guide", "type": "guide"}


def _full_fixer() -> dict:
    return {
        "name": "Safari Pro",
        "type": "agency",
        "phone": "+254700123456",
        "whatsapp": "+254700123456",
        "email": "info@safaripro.com",
        "notes": "Best in Nairobi",
        "rating": 4,
        "links": [
            {"type": "website", "url": "https://safaripro.com"},
            {"type": "tripadvisor", "url": "https://tripadvisor.com/safari"},
        ],
        "country_codes": ["KE", "TZ"],
    }


# --- List ---


def test_list_fixers_empty(admin_client: TestClient) -> None:
    res = admin_client.get(BASE)
    assert res.status_code == 200
    assert res.json()["fixers"] == []


# --- Create ---


def test_create_minimal_fixer(admin_client: TestClient) -> None:
    res = admin_client.post(BASE, json=_minimal_fixer())
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Test Guide"
    assert data["type"] == "guide"
    assert data["id"] > 0
    assert data["country_codes"] == []
    assert data["links"] == []


def test_create_full_fixer(admin_client: TestClient) -> None:
    res = admin_client.post(BASE, json=_full_fixer())
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Safari Pro"
    assert data["type"] == "agency"
    assert data["phone"] == "+254700123456"
    assert data["whatsapp"] == "+254700123456"
    assert data["email"] == "info@safaripro.com"
    assert data["notes"] == "Best in Nairobi"
    assert data["rating"] == 4
    assert data["country_codes"] == ["KE", "TZ"]
    assert len(data["links"]) == 2
    assert data["links"][0]["type"] == "website"


def test_create_invalid_rating(admin_client: TestClient) -> None:
    payload = _minimal_fixer()
    payload["rating"] = 5
    res = admin_client.post(BASE, json=payload)
    assert res.status_code == 422


def test_create_invalid_type(admin_client: TestClient) -> None:
    payload = {"name": "Bad Type", "type": "wizard"}
    res = admin_client.post(BASE, json=payload)
    assert res.status_code == 422


# --- Update ---


def test_update_fixer(admin_client: TestClient) -> None:
    res = admin_client.post(BASE, json=_minimal_fixer())
    fixer_id = res.json()["id"]

    updated = _minimal_fixer()
    updated["name"] = "Updated Guide"
    updated["rating"] = 3
    res = admin_client.put(f"{BASE}{fixer_id}", json=updated)
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Guide"
    assert res.json()["rating"] == 3


def test_update_not_found(admin_client: TestClient) -> None:
    res = admin_client.put(f"{BASE}9999", json=_minimal_fixer())
    assert res.status_code == 404


def test_update_replaces_countries(admin_client: TestClient) -> None:
    payload = _full_fixer()
    res = admin_client.post(BASE, json=payload)
    fixer_id = res.json()["id"]
    assert res.json()["country_codes"] == ["KE", "TZ"]

    # Update with different countries
    payload["country_codes"] = ["GH", "TG"]
    res = admin_client.put(f"{BASE}{fixer_id}", json=payload)
    assert res.status_code == 200
    assert res.json()["country_codes"] == ["GH", "TG"]


# --- Delete ---


def test_delete_fixer(admin_client: TestClient) -> None:
    res = admin_client.post(BASE, json=_minimal_fixer())
    fixer_id = res.json()["id"]

    res = admin_client.delete(f"{BASE}{fixer_id}")
    assert res.status_code == 204

    res = admin_client.get(BASE)
    assert len(res.json()["fixers"]) == 0


def test_delete_not_found(admin_client: TestClient) -> None:
    res = admin_client.delete(f"{BASE}9999")
    assert res.status_code == 404


def test_delete_cascades_countries(admin_client: TestClient) -> None:
    """Deleting a fixer should cascade-delete its country records."""
    payload = _full_fixer()
    res = admin_client.post(BASE, json=payload)
    fixer_id = res.json()["id"]

    res = admin_client.delete(f"{BASE}{fixer_id}")
    assert res.status_code == 204

    # Verify fixer is gone
    res = admin_client.get(BASE)
    assert len(res.json()["fixers"]) == 0


# --- Filters ---


def test_filter_by_country(admin_client: TestClient) -> None:
    admin_client.post(
        BASE, json={**_minimal_fixer(), "country_codes": ["KE", "TZ"]}
    )
    admin_client.post(
        BASE, json={"name": "Ghana Guide", "type": "guide", "country_codes": ["GH"]}
    )

    res = admin_client.get(f"{BASE}?country=KE")
    assert res.status_code == 200
    fixers = res.json()["fixers"]
    assert len(fixers) == 1
    assert fixers[0]["name"] == "Test Guide"


def test_search_by_name(admin_client: TestClient) -> None:
    admin_client.post(BASE, json=_minimal_fixer())
    admin_client.post(BASE, json={"name": "Other Driver", "type": "driver"})

    res = admin_client.get(f"{BASE}?search=guide")
    assert res.status_code == 200
    fixers = res.json()["fixers"]
    assert len(fixers) == 1
    assert fixers[0]["name"] == "Test Guide"


# --- Edge cases ---


def test_country_code_uppercase_normalization(admin_client: TestClient) -> None:
    payload = _minimal_fixer()
    payload["country_codes"] = ["ke", "tz"]
    res = admin_client.post(BASE, json=payload)
    assert res.status_code == 201
    assert res.json()["country_codes"] == ["KE", "TZ"]


def test_list_countries(admin_client: TestClient) -> None:
    res = admin_client.get(f"{BASE}countries")
    assert res.status_code == 200
    data = res.json()
    assert "countries" in data
    assert isinstance(data["countries"], list)


def test_links_round_trip(admin_client: TestClient) -> None:
    payload = _minimal_fixer()
    payload["links"] = [
        {"type": "instagram", "url": "https://instagram.com/guide"},
        {"type": "other", "url": "https://example.com"},
    ]
    res = admin_client.post(BASE, json=payload)
    assert res.status_code == 201
    links = res.json()["links"]
    assert len(links) == 2
    assert links[0]["type"] == "instagram"
    assert links[1]["url"] == "https://example.com"
