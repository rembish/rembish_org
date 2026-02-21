"""Tests for transport bookings API (trains, buses, ferries)."""

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.extraction import ExtractedTransportBooking, TransportBookingExtractionResult
from src.models import TransportBooking, Trip


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


def test_list_transport_bookings_empty(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/transport-bookings")
    assert res.status_code == 200
    data = res.json()
    assert data["transport_bookings"] == []


def test_create_transport_booking_train(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings",
        json={
            "type": "train",
            "operator": "České dráhy",
            "service_number": "EC 171",
            "departure_station": "Praha hlavní nádraží",
            "arrival_station": "Wien Hauptbahnhof",
            "departure_datetime": "2026-03-15 08:30",
            "arrival_datetime": "2026-03-15 12:45",
            "carriage": "26",
            "seat": "45",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "train"
    assert data["operator"] == "České dráhy"
    assert data["service_number"] == "EC 171"
    assert data["departure_station"] == "Praha hlavní nádraží"
    assert data["arrival_station"] == "Wien Hauptbahnhof"
    assert data["carriage"] == "26"
    assert data["seat"] == "45"
    assert data["id"] > 0


def test_create_transport_booking_bus(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings",
        json={
            "type": "bus",
            "operator": "FlixBus",
            "service_number": "N123",
        },
    )
    assert res.status_code == 200
    assert res.json()["type"] == "bus"
    assert res.json()["operator"] == "FlixBus"


def test_create_transport_booking_ferry(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings",
        json={
            "type": "ferry",
            "operator": "Viking Line",
        },
    )
    assert res.status_code == 200
    assert res.json()["type"] == "ferry"


def test_create_transport_booking_minimal(admin_client: TestClient, db_session: Session) -> None:
    """Only type is required."""
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings",
        json={"type": "train"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "train"
    assert data["operator"] is None
    assert data["service_number"] is None


def test_create_transport_booking_invalid_type(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings",
        json={"type": "airplane"},
    )
    assert res.status_code == 422


def test_update_transport_booking(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    create_res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings",
        json={"type": "train", "operator": "ÖBB"},
    )
    booking_id = create_res.json()["id"]

    res = admin_client.put(
        f"/api/v1/travels/transport-bookings/{booking_id}",
        json={
            "type": "train",
            "operator": "ÖBB",
            "seat": "12A",
            "carriage": "5",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["seat"] == "12A"
    assert data["carriage"] == "5"


def test_delete_transport_booking(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    booking = TransportBooking(
        trip_id=trip.id,
        type="train",
        operator="DB",
        departure_datetime="2026-03-15 09:00",
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    res = admin_client.delete(f"/api/v1/travels/transport-bookings/{booking.id}")
    assert res.status_code == 204

    assert (
        db_session.query(TransportBooking).filter(TransportBooking.id == booking.id).first() is None
    )


def test_delete_transport_booking_not_found(admin_client: TestClient) -> None:
    res = admin_client.delete("/api/v1/travels/transport-bookings/999")
    assert res.status_code == 404


def test_transport_bookings_require_auth(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = client.get(f"/api/v1/travels/trips/{trip.id}/transport-bookings")
    assert res.status_code == 401


def test_transport_bookings_ordered_by_departure(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)

    # Create in reverse order
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings",
        json={
            "type": "train",
            "operator": "DB",
            "departure_datetime": "2026-03-20 10:00",
        },
    )
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings",
        json={
            "type": "bus",
            "operator": "FlixBus",
            "departure_datetime": "2026-03-15 10:00",
        },
    )

    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/transport-bookings")
    bookings = res.json()["transport_bookings"]
    assert len(bookings) == 2
    assert bookings[0]["operator"] == "FlixBus"
    assert bookings[1]["operator"] == "DB"


def test_create_transport_booking_trip_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/trips/9999/transport-bookings",
        json={"type": "train"},
    )
    assert res.status_code == 404


def test_transport_booking_reference_masked(db_session: Session) -> None:
    """Booking reference masked value is stored correctly."""
    from src.crypto import mask_value

    trip = _create_trip(db_session)

    masked = mask_value("ABC123456", reveal=1)
    booking = TransportBooking(
        trip_id=trip.id,
        type="train",
        operator="DB",
        booking_reference_masked=masked,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    assert booking.booking_reference_masked is not None
    assert "6" in booking.booking_reference_masked  # last char revealed
    assert "A" in booking.booking_reference_masked  # first char revealed


@patch("src.travels.transport_bookings.extract_transport_booking_data")
def test_extract_transport_booking_endpoint(
    mock_extract: object, admin_client: TestClient, db_session: Session
) -> None:
    """POST /trips/{id}/transport-bookings/extract returns extracted booking data."""
    mock_extract = mock_extract  # type: ignore[assignment]
    assert isinstance(mock_extract, MagicMock)
    trip = _create_trip(db_session)

    mock_extract.return_value = TransportBookingExtractionResult(
        booking=ExtractedTransportBooking(
            type="train",
            operator="České dráhy",
            service_number="EC 171",
            departure_station="Praha hlavní nádraží",
            arrival_station="Wien Hauptbahnhof",
            departure_datetime="2026-03-15 08:30",
            arrival_datetime="2026-03-15 12:45",
            carriage="26",
            seat="45",
            booking_reference="ABC123456",
        )
    )

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings/extract",
        files={"file": ("ticket.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["booking"]["type"] == "train"
    assert data["booking"]["operator"] == "České dráhy"
    assert data["booking"]["is_duplicate"] is False
    assert data["error"] is None


@patch("src.travels.transport_bookings.extract_transport_booking_data")
def test_extract_transport_booking_dedup(
    mock_extract: object, admin_client: TestClient, db_session: Session
) -> None:
    """Extracted booking matching existing one is marked as duplicate."""
    mock_extract = mock_extract  # type: ignore[assignment]
    assert isinstance(mock_extract, MagicMock)
    trip = _create_trip(db_session)

    # Create existing booking
    db_session.add(
        TransportBooking(
            trip_id=trip.id,
            type="train",
            operator="České dráhy",
            departure_datetime="2026-03-15 08:30",
        )
    )
    db_session.commit()

    mock_extract.return_value = TransportBookingExtractionResult(
        booking=ExtractedTransportBooking(
            type="train",
            operator="České dráhy",
            departure_datetime="2026-03-15 08:30",
        )
    )

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/transport-bookings/extract",
        files={"file": ("ticket.pdf", b"fake-pdf", "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["booking"]["is_duplicate"] is True


def test_extract_transport_booking_trip_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/trips/9999/transport-bookings/extract",
        files={"file": ("ticket.pdf", b"fake-pdf", "application/pdf")},
    )
    assert res.status_code == 404


def test_transport_booking_document_upload(admin_client: TestClient, db_session: Session) -> None:
    """Upload a document to a transport booking."""
    trip = _create_trip(db_session)

    booking = TransportBooking(
        trip_id=trip.id,
        type="train",
        operator="DB",
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    with patch("src.vault_storage.get_vault_storage") as mock_storage_fn:
        mock_storage = MagicMock()
        mock_storage.save.return_value = "1/abc123.pdf"
        mock_storage_fn.return_value = mock_storage

        res = admin_client.post(
            f"/api/v1/travels/transport-bookings/{booking.id}/document",
            files={"file": ("ticket.pdf", b"fake-pdf-content", "application/pdf")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["has_document"] is True
        assert data["document_name"] == "ticket.pdf"
        mock_storage.save.assert_called_once()


def test_transport_booking_document_get_url(admin_client: TestClient, db_session: Session) -> None:
    """Get signed URL for a transport booking document."""
    trip = _create_trip(db_session)

    booking = TransportBooking(
        trip_id=trip.id,
        type="ferry",
        operator="Viking Line",
        document_path="1/abc123.pdf",
        document_name="ticket.pdf",
        document_mime_type="application/pdf",
        document_size=1024,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    with patch("src.vault_storage.get_vault_storage") as mock_storage_fn:
        mock_storage = MagicMock()
        mock_storage.get_signed_url.return_value = "https://example.com/signed-url"
        mock_storage_fn.return_value = mock_storage

        res = admin_client.get(f"/api/v1/travels/transport-bookings/{booking.id}/document")
        assert res.status_code == 200
        data = res.json()
        assert data["url"] == "https://example.com/signed-url"


def test_transport_booking_document_delete(admin_client: TestClient, db_session: Session) -> None:
    """Delete document from a transport booking."""
    trip = _create_trip(db_session)

    booking = TransportBooking(
        trip_id=trip.id,
        type="bus",
        operator="FlixBus",
        document_path="1/abc123.pdf",
        document_name="ticket.pdf",
        document_mime_type="application/pdf",
        document_size=1024,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    with patch("src.vault_storage.get_vault_storage") as mock_storage_fn:
        mock_storage = MagicMock()
        mock_storage_fn.return_value = mock_storage

        res = admin_client.delete(f"/api/v1/travels/transport-bookings/{booking.id}/document")
        assert res.status_code == 204
        mock_storage.delete.assert_called_once()

    db_session.refresh(booking)
    assert booking.document_path is None
    assert booking.document_name is None
