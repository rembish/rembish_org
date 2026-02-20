"""Tests for personal events CRUD API."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import PersonalEvent


def _create_event(
    db: Session,
    event_date: str = "2026-03-15",
    title: str = "Doctor appointment",
    note: str | None = None,
    category: str = "medical",
) -> PersonalEvent:
    event = PersonalEvent(
        event_date=date.fromisoformat(event_date),
        title=title,
        note=note,
        category=category,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_list_events_empty(admin_client: TestClient) -> None:
    res = admin_client.get("/api/v1/travels/events")
    assert res.status_code == 200
    data = res.json()
    assert data["events"] == []
    assert data["total"] == 0
    assert "medical" in data["categories"]
    assert "other" in data["categories"]


def test_list_events(admin_client: TestClient, db_session: Session) -> None:
    _create_event(db_session, "2026-03-10", "Car service", category="car")
    _create_event(db_session, "2026-03-20", "Dentist", category="medical")

    res = admin_client.get("/api/v1/travels/events")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["events"][0]["title"] == "Car service"
    assert data["events"][0]["event_date"] == "2026-03-10"
    assert data["events"][1]["title"] == "Dentist"


def test_get_event(admin_client: TestClient, db_session: Session) -> None:
    event = _create_event(db_session, note="Annual checkup")

    res = admin_client.get(f"/api/v1/travels/events/{event.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Doctor appointment"
    assert data["note"] == "Annual checkup"
    assert data["category"] == "medical"
    assert data["category_emoji"] == "\U0001f3e5"


def test_get_event_not_found(admin_client: TestClient) -> None:
    res = admin_client.get("/api/v1/travels/events/999")
    assert res.status_code == 404


def test_create_event(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/events",
        json={
            "event_date": "2026-04-01",
            "title": "Concert tickets",
            "note": "Gate opens at 10am",
            "category": "event",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Concert tickets"
    assert data["event_date"] == "2026-04-01"
    assert data["category"] == "event"
    assert data["category_emoji"] == "\U0001f389"
    assert data["note"] == "Gate opens at 10am"
    assert data["id"] > 0


def test_create_event_minimal(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/events",
        json={"event_date": "2026-05-01", "title": "Something"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["category"] == "other"
    assert data["note"] is None
    assert data["end_date"] is None


def test_create_event_multiday(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/events",
        json={
            "event_date": "2026-06-05",
            "end_date": "2026-06-07",
            "title": "Comic Con",
            "category": "event",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["event_date"] == "2026-06-05"
    assert data["end_date"] == "2026-06-07"
    assert data["title"] == "Comic Con"


def test_create_event_invalid_category(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/events",
        json={
            "event_date": "2026-04-01",
            "title": "Test",
            "category": "nonexistent",
        },
    )
    assert res.status_code == 422


def test_update_event(admin_client: TestClient, db_session: Session) -> None:
    event = _create_event(db_session)

    res = admin_client.put(
        f"/api/v1/travels/events/{event.id}",
        json={"title": "Updated title", "category": "car"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Updated title"
    assert data["category"] == "car"
    # Unchanged fields preserved
    assert data["event_date"] == "2026-03-15"


def test_update_event_not_found(admin_client: TestClient) -> None:
    res = admin_client.put(
        "/api/v1/travels/events/999",
        json={"title": "Nope"},
    )
    assert res.status_code == 404


def test_update_event_invalid_category(admin_client: TestClient, db_session: Session) -> None:
    event = _create_event(db_session)

    res = admin_client.put(
        f"/api/v1/travels/events/{event.id}",
        json={"category": "bad"},
    )
    assert res.status_code == 422


def test_delete_event(admin_client: TestClient, db_session: Session) -> None:
    event = _create_event(db_session)

    res = admin_client.delete(f"/api/v1/travels/events/{event.id}")
    assert res.status_code == 204

    # Verify deleted
    res = admin_client.get(f"/api/v1/travels/events/{event.id}")
    assert res.status_code == 404


def test_delete_event_not_found(admin_client: TestClient) -> None:
    res = admin_client.delete("/api/v1/travels/events/999")
    assert res.status_code == 404


def test_events_require_admin(client: TestClient) -> None:
    res = client.get("/api/v1/travels/events")
    assert res.status_code == 401


def test_event_categories_complete(admin_client: TestClient) -> None:
    res = admin_client.get("/api/v1/travels/events")
    categories = res.json()["categories"]
    expected = {
        "medical",
        "car",
        "event",
        "admin",
        "social",
        "home",
        "pet",
        "photo",
        "boardgames",
        "other",
    }
    assert set(categories.keys()) == expected
