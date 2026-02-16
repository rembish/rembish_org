"""Tests for the contact form endpoint."""

import time
from unittest.mock import patch

from fastapi.testclient import TestClient


def _valid_form(ts: str | None = None) -> dict[str, str]:
    """Return valid form data with a realistic timestamp."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "message": "This is a test message with enough length.",
        "website": "",
        "ts": ts or str(int(time.time() * 1000) - 5000),
        "cf_turnstile_response": "",
    }


def test_contact_success(client: TestClient) -> None:
    """Successful contact form submission."""
    with patch("src.main.send_telegram_message", return_value=True):
        response = client.post("/api/v1/contact", data=_valid_form())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["message"] == "Message sent successfully"


def test_contact_honeypot_rejected(client: TestClient) -> None:
    """Honeypot field filled = silently rejected."""
    form = _valid_form()
    form["website"] = "http://spam.com"
    response = client.post("/api/v1/contact", data=form)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "message" not in data  # Silent rejection, no success message


def test_contact_speed_check_rejected(client: TestClient) -> None:
    """Form submitted too fast = silently rejected."""
    form = _valid_form(ts=str(int(time.time() * 1000)))  # Just now
    response = client.post("/api/v1/contact", data=form)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "message" not in data  # Silent rejection


def test_contact_name_too_short(client: TestClient) -> None:
    """Name shorter than min_length is rejected."""
    form = _valid_form()
    form["name"] = "A"
    response = client.post("/api/v1/contact", data=form)
    assert response.status_code == 422


def test_contact_message_too_short(client: TestClient) -> None:
    """Message shorter than min_length is rejected."""
    form = _valid_form()
    form["message"] = "Short"
    response = client.post("/api/v1/contact", data=form)
    assert response.status_code == 422


def test_contact_name_max_length(client: TestClient) -> None:
    """Name exceeding max_length is rejected."""
    form = _valid_form()
    form["name"] = "A" * 256
    response = client.post("/api/v1/contact", data=form)
    assert response.status_code == 422


def test_contact_message_max_length(client: TestClient) -> None:
    """Message exceeding max_length is rejected."""
    form = _valid_form()
    form["message"] = "A" * 5001
    response = client.post("/api/v1/contact", data=form)
    assert response.status_code == 422


def test_contact_subject_max_length(client: TestClient) -> None:
    """Subject exceeding max_length is rejected."""
    form = _valid_form()
    form["subject"] = "A" * 256
    response = client.post("/api/v1/contact", data=form)
    assert response.status_code == 422


def test_contact_turnstile_skip_in_dev(client: TestClient) -> None:
    """Turnstile verification is skipped when secret is not configured."""
    with patch("src.main.send_telegram_message", return_value=True):
        response = client.post("/api/v1/contact", data=_valid_form())
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_contact_invalid_email(client: TestClient) -> None:
    """Invalid email is rejected."""
    form = _valid_form()
    form["email"] = "not-an-email"
    response = client.post("/api/v1/contact", data=form)
    assert response.status_code == 422
