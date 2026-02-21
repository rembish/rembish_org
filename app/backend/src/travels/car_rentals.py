import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth.session import (
    get_admin_user,
    get_trips_viewer,
    is_vault_unlocked,
    is_vault_unlocked_for_viewer,
)
from ..crypto import decrypt, encrypt, mask_value
from ..database import get_db
from ..extraction import extract_car_rental_data
from ..models import CarRental, Trip, User
from .models import (
    CarRentalCreateRequest,
    CarRentalData,
    CarRentalExtractResponse,
    CarRentalsResponse,
    ExtractedCarRentalResponse,
)

log = logging.getLogger(__name__)

router = APIRouter()

MAX_EXTRACT_SIZE = 10 * 1024 * 1024  # 10 MB
EXTRACT_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


def _confirmation_display(rental: CarRental, vault_open: bool) -> str | None:
    """Return decrypted confirmation number if vault is unlocked, masked otherwise."""
    if not rental.confirmation_number_encrypted and not rental.confirmation_number_masked:
        return None
    if rental.confirmation_number_encrypted:
        try:
            plaintext = decrypt(rental.confirmation_number_encrypted)
            return plaintext if vault_open else mask_value(plaintext, reveal=1)
        except Exception:
            pass
    return rental.confirmation_number_masked


def _rental_to_data(rental: CarRental, vault_open: bool = False) -> CarRentalData:
    return CarRentalData(
        id=rental.id,
        trip_id=rental.trip_id,
        rental_company=rental.rental_company,
        car_class=rental.car_class,
        actual_car=rental.actual_car,
        transmission=rental.transmission,
        pickup_location=rental.pickup_location,
        dropoff_location=rental.dropoff_location,
        pickup_datetime=rental.pickup_datetime,
        dropoff_datetime=rental.dropoff_datetime,
        is_paid=rental.is_paid,
        total_amount=rental.total_amount,
        confirmation_number=_confirmation_display(rental, vault_open),
        notes=rental.notes,
    )


@router.post("/trips/{trip_id}/car-rentals/extract", response_model=CarRentalExtractResponse)
async def extract_car_rental_from_pdf(
    trip_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> CarRentalExtractResponse:
    """Upload a car rental PDF/image and extract data via AI."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    content_type = file.content_type or ""
    if content_type not in EXTRACT_MIME_TYPES:
        return CarRentalExtractResponse(
            error=f"Unsupported file type: {content_type}. Use PDF or image."
        )

    content = await file.read()
    if len(content) > MAX_EXTRACT_SIZE:
        return CarRentalExtractResponse(error="File too large (max 10 MB)")

    result = extract_car_rental_data(content, content_type)
    if result.error:
        return CarRentalExtractResponse(error=result.error)
    if not result.rental:
        return CarRentalExtractResponse(error="No rental data extracted")

    # Check for duplicates: same pickup_datetime + rental_company
    is_dup = False
    if result.rental.pickup_datetime and result.rental.rental_company:
        existing = (
            db.query(CarRental)
            .filter(
                CarRental.trip_id == trip_id,
                CarRental.pickup_datetime == result.rental.pickup_datetime,
                CarRental.rental_company == result.rental.rental_company,
            )
            .first()
        )
        is_dup = existing is not None

    extracted = ExtractedCarRentalResponse(
        rental_company=result.rental.rental_company,
        car_class=result.rental.car_class,
        transmission=result.rental.transmission,
        pickup_location=result.rental.pickup_location,
        dropoff_location=result.rental.dropoff_location,
        pickup_datetime=result.rental.pickup_datetime,
        dropoff_datetime=result.rental.dropoff_datetime,
        is_paid=result.rental.is_paid,
        total_amount=result.rental.total_amount,
        confirmation_number=result.rental.confirmation_number,
        notes=result.rental.notes,
        is_duplicate=is_dup,
    )

    return CarRentalExtractResponse(rental=extracted)


@router.get("/trips/{trip_id}/car-rentals", response_model=CarRentalsResponse)
def get_trip_car_rentals(
    trip_id: int,
    viewer: Annotated[User, Depends(get_trips_viewer)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked_for_viewer)],
    db: Session = Depends(get_db),
) -> CarRentalsResponse:
    """Get all car rentals for a trip, ordered by pickup datetime."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    rentals = (
        db.query(CarRental)
        .filter(CarRental.trip_id == trip_id)
        .order_by(CarRental.pickup_datetime)
        .all()
    )

    return CarRentalsResponse(car_rentals=[_rental_to_data(r, vault_open) for r in rentals])


@router.post("/trips/{trip_id}/car-rentals", response_model=CarRentalData)
def create_car_rental(
    trip_id: int,
    request: CarRentalCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked)],
    db: Session = Depends(get_db),
) -> CarRentalData:
    """Create a car rental for a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    rental = CarRental(
        trip_id=trip_id,
        rental_company=request.rental_company,
        car_class=request.car_class,
        actual_car=request.actual_car,
        transmission=request.transmission,
        pickup_location=request.pickup_location,
        dropoff_location=request.dropoff_location,
        pickup_datetime=request.pickup_datetime,
        dropoff_datetime=request.dropoff_datetime,
        is_paid=request.is_paid,
        total_amount=request.total_amount,
        notes=request.notes,
    )
    if request.confirmation_number:
        rental.confirmation_number_encrypted = encrypt(request.confirmation_number)
        rental.confirmation_number_masked = mask_value(request.confirmation_number, reveal=1)
    db.add(rental)
    db.commit()
    db.refresh(rental)
    return _rental_to_data(rental, vault_open)


@router.put("/car-rentals/{rental_id}", response_model=CarRentalData)
def update_car_rental(
    rental_id: int,
    request: CarRentalCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked)],
    db: Session = Depends(get_db),
) -> CarRentalData:
    """Update a car rental (e.g., set actual_car after the rental)."""
    rental = db.query(CarRental).filter(CarRental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Car rental not found")

    rental.rental_company = request.rental_company
    rental.car_class = request.car_class
    rental.actual_car = request.actual_car
    rental.transmission = request.transmission
    rental.pickup_location = request.pickup_location
    rental.dropoff_location = request.dropoff_location
    rental.pickup_datetime = request.pickup_datetime
    rental.dropoff_datetime = request.dropoff_datetime
    rental.is_paid = request.is_paid
    rental.total_amount = request.total_amount
    rental.notes = request.notes

    if request.confirmation_number:
        rental.confirmation_number_encrypted = encrypt(request.confirmation_number)
        rental.confirmation_number_masked = mask_value(request.confirmation_number, reveal=1)
    else:
        rental.confirmation_number_encrypted = None
        rental.confirmation_number_masked = None

    db.commit()
    db.refresh(rental)
    return _rental_to_data(rental, vault_open)


@router.delete("/car-rentals/{rental_id}", status_code=204)
def delete_car_rental(
    rental_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a car rental."""
    rental = db.query(CarRental).filter(CarRental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Car rental not found")
    db.delete(rental)
    db.commit()
