"""Tests for ICS calendar feed."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import AppSetting, PersonalEvent, Trip, TripDestination


def _set_token(db: Session, token: str = "test-token-123") -> None:
    db.add(AppSetting(key="calendar_feed_token", value=token))
    db.commit()


def _create_trip(
    db: Session,
    start: str = "2026-03-01",
    end: str | None = "2026-03-05",
) -> Trip:
    trip = Trip(
        start_date=date.fromisoformat(start),
        end_date=date.fromisoformat(end) if end else None,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def _create_event(
    db: Session,
    event_date: str = "2026-04-10",
    title: str = "Doctor visit",
    category: str = "medical",
    note: str | None = None,
    end_date: str | None = None,
) -> PersonalEvent:
    event = PersonalEvent(
        event_date=date.fromisoformat(event_date),
        end_date=date.fromisoformat(end_date) if end_date else None,
        title=title,
        note=note,
        category=category,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_calendar_no_token(client: TestClient) -> None:
    """No token configured returns 404."""
    res = client.get("/api/v1/travels/calendar.ics?token=anything")
    assert res.status_code == 404


def test_calendar_invalid_token(client: TestClient, db_session: Session) -> None:
    """Invalid token returns 403."""
    _set_token(db_session, "correct-token")
    res = client.get("/api/v1/travels/calendar.ics?token=wrong-token")
    assert res.status_code == 403


def test_calendar_valid_token_empty(client: TestClient, db_session: Session) -> None:
    """Valid token with no trips/events returns valid ICS."""
    _set_token(db_session)
    res = client.get("/api/v1/travels/calendar.ics?token=test-token-123")
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/calendar; charset=utf-8"
    body = res.text
    assert "BEGIN:VCALENDAR" in body
    assert "END:VCALENDAR" in body


def test_calendar_with_trip(client: TestClient, db_session: Session) -> None:
    """ICS contains trip as VEVENT."""
    _set_token(db_session)
    _create_trip(db_session, "2026-06-01", "2026-06-10")

    res = client.get("/api/v1/travels/calendar.ics?token=test-token-123")
    assert res.status_code == 200
    body = res.text
    assert "BEGIN:VEVENT" in body
    assert "trip-" in body
    assert "DTSTART" in body


def test_calendar_with_event(client: TestClient, db_session: Session) -> None:
    """ICS contains personal event as VEVENT."""
    _set_token(db_session)
    _create_event(db_session, title="Dentist", category="medical", note="Annual checkup")

    res = client.get("/api/v1/travels/calendar.ics?token=test-token-123")
    assert res.status_code == 200
    body = res.text
    assert "BEGIN:VEVENT" in body
    assert "event-" in body
    assert "Dentist" in body


def test_calendar_event_has_note(client: TestClient, db_session: Session) -> None:
    """Event note appears in DESCRIPTION."""
    _set_token(db_session)
    _create_event(db_session, note="Bring insurance card")

    res = client.get("/api/v1/travels/calendar.ics?token=test-token-123")
    body = res.text
    assert "Bring insurance card" in body


def test_feed_token_none(admin_client: TestClient) -> None:
    """Feed token returns null when no token exists."""
    res = admin_client.get("/api/v1/travels/calendar/feed-token")
    assert res.status_code == 200
    assert res.json()["token"] is None


def test_feed_token_exists(admin_client: TestClient, db_session: Session) -> None:
    """Feed token returns the token value when it exists."""
    _set_token(db_session, "my-uuid-token")
    res = admin_client.get("/api/v1/travels/calendar/feed-token")
    assert res.status_code == 200
    assert res.json()["token"] == "my-uuid-token"


def test_feed_token_requires_admin(client: TestClient) -> None:
    """Feed token endpoint requires admin auth."""
    res = client.get("/api/v1/travels/calendar/feed-token")
    assert res.status_code == 401


def test_regenerate_token(admin_client: TestClient, db_session: Session) -> None:
    """Regenerate creates new token, old one stops working."""
    _set_token(db_session, "old-token")

    # Regenerate
    res = admin_client.post("/api/v1/travels/calendar/regenerate-token")
    assert res.status_code == 200
    new_token = res.json()["token"]
    assert new_token != "old-token"

    # Old token no longer works
    res = admin_client.get("/api/v1/travels/calendar.ics?token=old-token")
    assert res.status_code == 403

    # New token works
    res = admin_client.get(f"/api/v1/travels/calendar.ics?token={new_token}")
    assert res.status_code == 200


def test_regenerate_creates_first_token(admin_client: TestClient) -> None:
    """Regenerate works even when no token exists yet."""
    res = admin_client.post("/api/v1/travels/calendar/regenerate-token")
    assert res.status_code == 200
    assert res.json()["token"]


def test_regenerate_requires_admin(client: TestClient) -> None:
    """Regenerate endpoint requires admin auth."""
    res = client.post("/api/v1/travels/calendar/regenerate-token")
    assert res.status_code == 401
