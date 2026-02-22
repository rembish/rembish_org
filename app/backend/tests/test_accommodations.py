"""Tests for accommodations API (hotel/apartment bookings)."""

import base64
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.extraction import AccommodationExtractionResult, ExtractedAccommodation
from src.models import Accommodation, Trip

# Test encryption key: 32 zero bytes, base64-encoded
_TEST_KEY = base64.b64encode(b"\x00" * 32).decode()


def _create_trip(db: Session) -> Trip:
    trip = Trip(
        start_date=date(2026, 3, 10),
        end_date=date(2026, 3, 22),
        trip_type="regular",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def test_list_accommodations_empty(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/accommodations")
    assert res.status_code == 200
    data = res.json()
    assert data["accommodations"] == []


def test_create_accommodation_full(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={
            "property_name": "Hotel Marrakech",
            "platform": "booking",
            "checkin_date": "2026-03-12",
            "checkout_date": "2026-03-15",
            "address": "123 Main Street, Marrakech",
            "total_amount": "€245.00",
            "payment_status": "paid",
            "guests": 2,
            "rooms": 1,
            "booking_url": "https://www.booking.com/hotel/ma/marrakech.html",
            "notes": "Breakfast included",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["property_name"] == "Hotel Marrakech"
    assert data["platform"] == "booking"
    assert data["checkin_date"] == "2026-03-12"
    assert data["checkout_date"] == "2026-03-15"
    assert data["address"] == "123 Main Street, Marrakech"
    assert data["total_amount"] == "€245.00"
    assert data["payment_status"] == "paid"
    assert data["guests"] == 2
    assert data["rooms"] == 1
    assert data["booking_url"] == "https://www.booking.com/hotel/ma/marrakech.html"
    assert data["notes"] == "Breakfast included"
    assert data["id"] > 0


def test_create_accommodation_minimal(admin_client: TestClient, db_session: Session) -> None:
    """Only property_name is required."""
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={"property_name": "Riad Fes"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["property_name"] == "Riad Fes"
    assert data["platform"] is None
    assert data["checkin_date"] is None
    assert data["guests"] is None


def test_create_accommodation_invalid_platform(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={"property_name": "Test Hotel", "platform": "expedia"},
    )
    assert res.status_code == 422


def test_create_accommodation_invalid_payment_status(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={"property_name": "Test Hotel", "payment_status": "pending"},
    )
    assert res.status_code == 422


def test_create_accommodation_trip_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/trips/9999/accommodations",
        json={"property_name": "Test Hotel"},
    )
    assert res.status_code == 404


def test_update_accommodation(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    create_res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={"property_name": "Hotel A"},
    )
    acc_id = create_res.json()["id"]

    res = admin_client.put(
        f"/api/v1/travels/accommodations/{acc_id}",
        json={
            "property_name": "Hotel A (Updated)",
            "platform": "agoda",
            "checkin_date": "2026-03-14",
            "checkout_date": "2026-03-18",
            "total_amount": "$180.00",
            "payment_status": "pay_at_property",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["property_name"] == "Hotel A (Updated)"
    assert data["platform"] == "agoda"
    assert data["total_amount"] == "$180.00"
    assert data["payment_status"] == "pay_at_property"


def test_update_accommodation_not_found(admin_client: TestClient) -> None:
    res = admin_client.put(
        "/api/v1/travels/accommodations/999",
        json={"property_name": "X"},
    )
    assert res.status_code == 404


def test_delete_accommodation(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    acc = Accommodation(
        trip_id=trip.id,
        property_name="To Delete",
        checkin_date="2026-03-12",
    )
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)

    res = admin_client.delete(f"/api/v1/travels/accommodations/{acc.id}")
    assert res.status_code == 204

    assert db_session.query(Accommodation).filter(Accommodation.id == acc.id).first() is None


def test_delete_accommodation_not_found(admin_client: TestClient) -> None:
    res = admin_client.delete("/api/v1/travels/accommodations/999")
    assert res.status_code == 404


def test_accommodations_require_auth(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = client.get(f"/api/v1/travels/trips/{trip.id}/accommodations")
    assert res.status_code == 401


def test_accommodations_ordered_by_checkin(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)

    # Create in reverse order
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={"property_name": "Hotel B", "checkin_date": "2026-03-18"},
    )
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={"property_name": "Hotel A", "checkin_date": "2026-03-12"},
    )

    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/accommodations")
    accs = res.json()["accommodations"]
    assert len(accs) == 2
    assert accs[0]["property_name"] == "Hotel A"
    assert accs[1]["property_name"] == "Hotel B"


def test_accommodation_confirmation_code_masked(db_session: Session) -> None:
    """Confirmation code masked value is stored correctly."""
    from src.crypto import mask_value

    trip = _create_trip(db_session)

    masked = mask_value("CONF123456", reveal=1)
    acc = Accommodation(
        trip_id=trip.id,
        property_name="Test Hotel",
        confirmation_code_masked=masked,
    )
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)

    assert acc.confirmation_code_masked is not None
    assert "6" in acc.confirmation_code_masked  # last char revealed
    assert "C" in acc.confirmation_code_masked  # first char revealed


@patch("src.travels.accommodations.extract_accommodation_data")
def test_extract_accommodation_endpoint(
    mock_extract: object, admin_client: TestClient, db_session: Session
) -> None:
    """POST /trips/{id}/accommodations/extract returns extracted data."""
    mock_extract = mock_extract  # type: ignore[assignment]
    assert isinstance(mock_extract, MagicMock)
    trip = _create_trip(db_session)

    mock_extract.return_value = AccommodationExtractionResult(
        accommodation=ExtractedAccommodation(
            property_name="Grand Hotel",
            platform="booking",
            checkin_date="2026-03-12",
            checkout_date="2026-03-15",
            address="456 Avenue, Paris",
            total_amount="€320.00",
            payment_status="paid",
            guests=2,
            rooms=1,
            confirmation_code="BK-987654",
        )
    )

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations/extract",
        files={"file": ("booking.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["accommodation"]["property_name"] == "Grand Hotel"
    assert data["accommodation"]["platform"] == "booking"
    assert data["accommodation"]["is_duplicate"] is False
    assert data["error"] is None


@patch("src.travels.accommodations.extract_accommodation_data")
def test_extract_accommodation_dedup(
    mock_extract: object, admin_client: TestClient, db_session: Session
) -> None:
    """Extracted accommodation matching existing one is marked as duplicate."""
    mock_extract = mock_extract  # type: ignore[assignment]
    assert isinstance(mock_extract, MagicMock)
    trip = _create_trip(db_session)

    # Create existing accommodation
    db_session.add(
        Accommodation(
            trip_id=trip.id,
            property_name="Grand Hotel",
            checkin_date="2026-03-12",
        )
    )
    db_session.commit()

    mock_extract.return_value = AccommodationExtractionResult(
        accommodation=ExtractedAccommodation(
            property_name="Grand Hotel",
            checkin_date="2026-03-12",
        )
    )

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations/extract",
        files={"file": ("booking.pdf", b"fake-pdf", "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["accommodation"]["is_duplicate"] is True


@patch("src.travels.accommodations.extract_accommodation_data")
def test_extract_accommodation_error(
    mock_extract: object, admin_client: TestClient, db_session: Session
) -> None:
    """Extraction failure returns error."""
    mock_extract = mock_extract  # type: ignore[assignment]
    assert isinstance(mock_extract, MagicMock)
    trip = _create_trip(db_session)

    mock_extract.return_value = AccommodationExtractionResult(error="Extraction failed")

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations/extract",
        files={"file": ("booking.pdf", b"fake-pdf", "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["error"] == "Extraction failed"
    assert data["accommodation"] is None


def test_extract_accommodation_trip_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/trips/9999/accommodations/extract",
        files={"file": ("booking.pdf", b"fake-pdf", "application/pdf")},
    )
    assert res.status_code == 404


def test_extract_accommodation_unsupported_type(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations/extract",
        files={"file": ("booking.txt", b"fake-text", "text/plain")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "Unsupported file type" in data["error"]


def test_accommodation_document_upload(
    admin_client: TestClient, db_session: Session
) -> None:
    """Upload a document to an accommodation."""
    trip = _create_trip(db_session)

    acc = Accommodation(trip_id=trip.id, property_name="Hotel Test")
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)

    with patch("src.vault_storage.get_vault_storage") as mock_storage_fn:
        mock_storage = MagicMock()
        mock_storage.save.return_value = "1/abc123.pdf"
        mock_storage_fn.return_value = mock_storage

        res = admin_client.post(
            f"/api/v1/travels/accommodations/{acc.id}/document",
            files={"file": ("booking.pdf", b"fake-pdf-content", "application/pdf")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["has_document"] is True
        assert data["document_name"] == "booking.pdf"
        mock_storage.save.assert_called_once()


def test_accommodation_document_get_content(
    admin_client: TestClient, db_session: Session
) -> None:
    """Get document content streamed through the backend."""
    trip = _create_trip(db_session)

    acc = Accommodation(
        trip_id=trip.id,
        property_name="Hotel Test",
        document_path="1/abc123.pdf",
        document_name="booking.pdf",
        document_mime_type="application/pdf",
        document_size=2048,
    )
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)

    with patch("src.vault_storage.get_vault_storage") as mock_storage_fn:
        mock_storage = MagicMock()
        mock_storage.read.return_value = b"%PDF-fake-content"
        mock_storage_fn.return_value = mock_storage

        res = admin_client.get(f"/api/v1/travels/accommodations/{acc.id}/document")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert res.content == b"%PDF-fake-content"


def test_accommodation_document_get_no_document(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)

    acc = Accommodation(trip_id=trip.id, property_name="Hotel Test")
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)

    res = admin_client.get(f"/api/v1/travels/accommodations/{acc.id}/document")
    assert res.status_code == 404


def test_accommodation_document_delete(
    admin_client: TestClient, db_session: Session
) -> None:
    """Delete document from an accommodation."""
    trip = _create_trip(db_session)

    acc = Accommodation(
        trip_id=trip.id,
        property_name="Hotel Test",
        document_path="1/abc123.pdf",
        document_name="booking.pdf",
        document_mime_type="application/pdf",
        document_size=2048,
    )
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)

    with patch("src.vault_storage.get_vault_storage") as mock_storage_fn:
        mock_storage = MagicMock()
        mock_storage_fn.return_value = mock_storage

        res = admin_client.delete(f"/api/v1/travels/accommodations/{acc.id}/document")
        assert res.status_code == 204
        mock_storage.delete.assert_called_once()

    db_session.refresh(acc)
    assert acc.document_path is None
    assert acc.document_name is None


def test_accommodation_document_delete_no_document(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)

    acc = Accommodation(trip_id=trip.id, property_name="Hotel Test")
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)

    res = admin_client.delete(f"/api/v1/travels/accommodations/{acc.id}/document")
    assert res.status_code == 404


def test_delete_accommodation_with_document(
    admin_client: TestClient, db_session: Session
) -> None:
    """Deleting an accommodation also deletes its document from storage."""
    trip = _create_trip(db_session)

    acc = Accommodation(
        trip_id=trip.id,
        property_name="Hotel Test",
        document_path="1/abc123.pdf",
    )
    db_session.add(acc)
    db_session.commit()
    db_session.refresh(acc)

    with patch("src.vault_storage.get_vault_storage") as mock_storage_fn:
        mock_storage = MagicMock()
        mock_storage_fn.return_value = mock_storage

        res = admin_client.delete(f"/api/v1/travels/accommodations/{acc.id}")
        assert res.status_code == 204
        mock_storage.delete.assert_called_once_with("1/abc123.pdf")


def test_create_accommodation_with_confirmation_code(
    admin_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Confirmation code is encrypted when provided."""
    monkeypatch.setattr("src.config.settings.vault_encryption_key", _TEST_KEY)
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={
            "property_name": "Hotel Secure",
            "confirmation_code": "SECRET123",
        },
    )
    assert res.status_code == 200
    data = res.json()
    # Vault is locked in admin_client, so masked value is returned
    assert data["confirmation_code"] is not None

    # Verify encrypted in DB
    acc = db_session.query(Accommodation).filter(Accommodation.id == data["id"]).first()
    assert acc is not None
    assert acc.confirmation_code_encrypted is not None
    assert acc.confirmation_code_masked is not None


def test_update_accommodation_clears_confirmation_code(
    admin_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Updating without confirmation_code clears the encrypted value."""
    monkeypatch.setattr("src.config.settings.vault_encryption_key", _TEST_KEY)
    trip = _create_trip(db_session)

    create_res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations",
        json={
            "property_name": "Hotel Secure",
            "confirmation_code": "SECRET123",
        },
    )
    acc_id = create_res.json()["id"]

    res = admin_client.put(
        f"/api/v1/travels/accommodations/{acc_id}",
        json={"property_name": "Hotel Secure"},
    )
    assert res.status_code == 200
    assert res.json()["confirmation_code"] is None

    acc = db_session.query(Accommodation).filter(Accommodation.id == acc_id).first()
    assert acc is not None
    assert acc.confirmation_code_encrypted is None
    assert acc.confirmation_code_masked is None
