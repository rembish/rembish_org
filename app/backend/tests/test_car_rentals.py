"""Tests for car rental API."""

from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.extraction import CarRentalExtractionResult, ExtractedCarRental
from src.models import CarRental, Trip


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


def test_list_car_rentals_empty(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/car-rentals")
    assert res.status_code == 200
    data = res.json()
    assert data["car_rentals"] == []


def test_create_car_rental(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/car-rentals",
        json={
            "rental_company": "Hertz",
            "car_class": "Compact SUV",
            "transmission": "automatic",
            "pickup_location": "Keflavik Airport",
            "dropoff_location": "Keflavik Airport",
            "pickup_datetime": "2026-03-15 10:00",
            "dropoff_datetime": "2026-03-22 10:00",
            "is_paid": False,
            "total_amount": "\u20ac245.00",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["rental_company"] == "Hertz"
    assert data["car_class"] == "Compact SUV"
    assert data["transmission"] == "automatic"
    assert data["pickup_location"] == "Keflavik Airport"
    assert data["dropoff_location"] == "Keflavik Airport"
    assert data["is_paid"] is False
    assert data["total_amount"] == "\u20ac245.00"
    assert data["id"] > 0


def test_create_car_rental_minimal(admin_client: TestClient, db_session: Session) -> None:
    """Only rental_company is required."""
    trip = _create_trip(db_session)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/car-rentals",
        json={"rental_company": "Sixt"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["rental_company"] == "Sixt"
    assert data["car_class"] is None
    assert data["actual_car"] is None


def test_update_car_rental_actual_car(admin_client: TestClient, db_session: Session) -> None:
    """PUT allows setting actual_car without overwriting car_class."""
    trip = _create_trip(db_session)

    # Create rental with car_class
    create_res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/car-rentals",
        json={
            "rental_company": "Europcar",
            "car_class": "Economy",
        },
    )
    rental_id = create_res.json()["id"]

    # Update with actual_car
    res = admin_client.put(
        f"/api/v1/travels/car-rentals/{rental_id}",
        json={
            "rental_company": "Europcar",
            "car_class": "Economy",
            "actual_car": "Toyota Corolla",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["car_class"] == "Economy"
    assert data["actual_car"] == "Toyota Corolla"


def test_delete_car_rental(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    rental = CarRental(
        trip_id=trip.id,
        rental_company="Budget",
        pickup_datetime="2026-03-15 09:00",
    )
    db_session.add(rental)
    db_session.commit()
    db_session.refresh(rental)

    res = admin_client.delete(f"/api/v1/travels/car-rentals/{rental.id}")
    assert res.status_code == 204

    assert db_session.query(CarRental).filter(CarRental.id == rental.id).first() is None


def test_delete_car_rental_not_found(admin_client: TestClient) -> None:
    res = admin_client.delete("/api/v1/travels/car-rentals/999")
    assert res.status_code == 404


def test_car_rentals_require_auth(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = client.get(f"/api/v1/travels/trips/{trip.id}/car-rentals")
    assert res.status_code == 401


def test_car_rentals_ordered_by_pickup(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)

    # Create in reverse order
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/car-rentals",
        json={
            "rental_company": "Hertz",
            "pickup_datetime": "2026-03-20 10:00",
        },
    )
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/car-rentals",
        json={
            "rental_company": "Sixt",
            "pickup_datetime": "2026-03-15 10:00",
        },
    )

    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/car-rentals")
    rentals = res.json()["car_rentals"]
    assert len(rentals) == 2
    assert rentals[0]["rental_company"] == "Sixt"
    assert rentals[1]["rental_company"] == "Hertz"


def test_create_car_rental_trip_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/trips/9999/car-rentals",
        json={"rental_company": "Hertz"},
    )
    assert res.status_code == 404


@patch("src.travels.car_rentals.extract_car_rental_data")
def test_extract_car_rental_endpoint(
    mock_extract: object, admin_client: TestClient, db_session: Session
) -> None:
    """POST /trips/{id}/car-rentals/extract returns extracted rental data."""
    from unittest.mock import MagicMock

    mock_extract = mock_extract  # type: ignore[assignment]
    assert isinstance(mock_extract, MagicMock)
    trip = _create_trip(db_session)

    mock_extract.return_value = CarRentalExtractionResult(
        rental=ExtractedCarRental(
            rental_company="Hertz",
            car_class="Compact SUV",
            transmission="automatic",
            pickup_location="Keflavik Airport",
            dropoff_location="Keflavik Airport",
            pickup_datetime="2026-03-15 10:00",
            dropoff_datetime="2026-03-22 10:00",
            is_paid=False,
            total_amount="\u20ac245.00",
            confirmation_number="L2912369773",
        )
    )

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/car-rentals/extract",
        files={"file": ("rental.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["rental"]["rental_company"] == "Hertz"
    assert data["rental"]["car_class"] == "Compact SUV"
    assert data["rental"]["is_duplicate"] is False
    assert data["error"] is None


@patch("src.travels.car_rentals.extract_car_rental_data")
def test_extract_car_rental_dedup(
    mock_extract: object, admin_client: TestClient, db_session: Session
) -> None:
    """Extracted rental matching existing one is marked as duplicate."""
    from unittest.mock import MagicMock

    mock_extract = mock_extract  # type: ignore[assignment]
    assert isinstance(mock_extract, MagicMock)
    trip = _create_trip(db_session)

    # Create existing rental
    db_session.add(
        CarRental(
            trip_id=trip.id,
            rental_company="Hertz",
            pickup_datetime="2026-03-15 10:00",
        )
    )
    db_session.commit()

    mock_extract.return_value = CarRentalExtractionResult(
        rental=ExtractedCarRental(
            rental_company="Hertz",
            pickup_datetime="2026-03-15 10:00",
        )
    )

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/car-rentals/extract",
        files={"file": ("rental.pdf", b"fake-pdf", "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["rental"]["is_duplicate"] is True


def test_extract_car_rental_trip_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/trips/9999/car-rentals/extract",
        files={"file": ("rental.pdf", b"fake-pdf", "application/pdf")},
    )
    assert res.status_code == 404


def test_car_rental_confirmation_masked(db_session: Session) -> None:
    """Confirmation number masked value is stored correctly."""
    from src.crypto import mask_value

    trip = _create_trip(db_session)

    # Create rental directly with masked value (as would happen with encryption)
    masked = mask_value("L2912369773", reveal=1)
    rental = CarRental(
        trip_id=trip.id,
        rental_company="Hertz",
        confirmation_number_masked=masked,
    )
    db_session.add(rental)
    db_session.commit()
    db_session.refresh(rental)

    assert rental.confirmation_number_masked is not None
    assert "3" in rental.confirmation_number_masked  # last char revealed
    assert "L" in rental.confirmation_number_masked  # first char revealed
