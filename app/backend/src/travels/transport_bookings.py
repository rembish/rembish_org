import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from ..auth.session import (
    get_admin_user,
    get_trips_viewer,
    is_vault_unlocked,
    is_vault_unlocked_for_viewer,
)
from ..crypto import decrypt, encrypt, mask_value
from ..database import get_db
from ..extraction import extract_transport_booking_data
from ..models import TransportBooking, Trip, User
from .models import (
    ExtractedTransportBookingResponse,
    TransportBookingCreateRequest,
    TransportBookingData,
    TransportBookingExtractResponse,
    TransportBookingsResponse,
)

log = logging.getLogger(__name__)

router = APIRouter()

MAX_EXTRACT_SIZE = 10 * 1024 * 1024  # 10 MB
EXTRACT_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
VALID_TYPES = {"train", "bus", "ferry"}
DOC_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
MAX_DOC_SIZE = 10 * 1024 * 1024  # 10 MB


def _booking_ref_display(booking: TransportBooking, vault_open: bool) -> str | None:
    """Return decrypted booking reference if vault is unlocked, masked otherwise."""
    if not booking.booking_reference_encrypted and not booking.booking_reference_masked:
        return None
    if booking.booking_reference_encrypted:
        try:
            plaintext = decrypt(booking.booking_reference_encrypted)
            return plaintext if vault_open else mask_value(plaintext, reveal=1)
        except Exception:
            pass
    return booking.booking_reference_masked


def _booking_to_data(booking: TransportBooking, vault_open: bool = False) -> TransportBookingData:
    return TransportBookingData(
        id=booking.id,
        trip_id=booking.trip_id,
        type=booking.type,
        operator=booking.operator,
        service_number=booking.service_number,
        departure_station=booking.departure_station,
        arrival_station=booking.arrival_station,
        departure_datetime=booking.departure_datetime,
        arrival_datetime=booking.arrival_datetime,
        carriage=booking.carriage,
        seat=booking.seat,
        booking_reference=_booking_ref_display(booking, vault_open),
        has_document=booking.document_path is not None,
        document_name=booking.document_name,
        document_mime_type=booking.document_mime_type,
        document_size=booking.document_size,
        notes=booking.notes,
    )


@router.post(
    "/trips/{trip_id}/transport-bookings/extract",
    response_model=TransportBookingExtractResponse,
)
async def extract_transport_booking(
    trip_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> TransportBookingExtractResponse:
    """Upload a transport ticket PDF/image and extract data via AI."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    content_type = file.content_type or ""
    if content_type not in EXTRACT_MIME_TYPES:
        return TransportBookingExtractResponse(
            error=f"Unsupported file type: {content_type}. Use PDF or image."
        )

    content = await file.read()
    if len(content) > MAX_EXTRACT_SIZE:
        return TransportBookingExtractResponse(error="File too large (max 10 MB)")

    result = extract_transport_booking_data(content, content_type)
    if result.error:
        return TransportBookingExtractResponse(error=result.error)
    if not result.booking:
        return TransportBookingExtractResponse(error="No booking data extracted")

    # Check for duplicates: same departure_datetime + operator + type
    is_dup = False
    if result.booking.departure_datetime and result.booking.operator and result.booking.type:
        existing = (
            db.query(TransportBooking)
            .filter(
                TransportBooking.trip_id == trip_id,
                TransportBooking.departure_datetime == result.booking.departure_datetime,
                TransportBooking.operator == result.booking.operator,
                TransportBooking.type == result.booking.type,
            )
            .first()
        )
        is_dup = existing is not None

    extracted = ExtractedTransportBookingResponse(
        type=result.booking.type,
        operator=result.booking.operator,
        service_number=result.booking.service_number,
        departure_station=result.booking.departure_station,
        arrival_station=result.booking.arrival_station,
        departure_datetime=result.booking.departure_datetime,
        arrival_datetime=result.booking.arrival_datetime,
        carriage=result.booking.carriage,
        seat=result.booking.seat,
        booking_reference=result.booking.booking_reference,
        notes=result.booking.notes,
        is_duplicate=is_dup,
    )

    return TransportBookingExtractResponse(booking=extracted)


@router.get(
    "/trips/{trip_id}/transport-bookings",
    response_model=TransportBookingsResponse,
)
def get_trip_transport_bookings(
    trip_id: int,
    viewer: Annotated[User, Depends(get_trips_viewer)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked_for_viewer)],
    db: Session = Depends(get_db),
) -> TransportBookingsResponse:
    """Get all transport bookings for a trip, ordered by departure datetime."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    bookings = (
        db.query(TransportBooking)
        .filter(TransportBooking.trip_id == trip_id)
        .order_by(TransportBooking.departure_datetime)
        .all()
    )

    return TransportBookingsResponse(
        transport_bookings=[_booking_to_data(b, vault_open) for b in bookings]
    )


@router.post(
    "/trips/{trip_id}/transport-bookings",
    response_model=TransportBookingData,
)
def create_transport_booking(
    trip_id: int,
    request: TransportBookingCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked)],
    db: Session = Depends(get_db),
) -> TransportBookingData:
    """Create a transport booking for a trip."""
    if request.type not in VALID_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid type: {request.type}. "
            f"Must be one of: {', '.join(sorted(VALID_TYPES))}",
        )

    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    booking = TransportBooking(
        trip_id=trip_id,
        type=request.type,
        operator=request.operator,
        service_number=request.service_number,
        departure_station=request.departure_station,
        arrival_station=request.arrival_station,
        departure_datetime=request.departure_datetime,
        arrival_datetime=request.arrival_datetime,
        carriage=request.carriage,
        seat=request.seat,
        notes=request.notes,
    )
    if request.booking_reference:
        booking.booking_reference_encrypted = encrypt(request.booking_reference)
        booking.booking_reference_masked = mask_value(request.booking_reference, reveal=1)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _booking_to_data(booking, vault_open)


@router.put("/transport-bookings/{booking_id}", response_model=TransportBookingData)
def update_transport_booking(
    booking_id: int,
    request: TransportBookingCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked)],
    db: Session = Depends(get_db),
) -> TransportBookingData:
    """Update a transport booking."""
    if request.type not in VALID_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid type: {request.type}. "
            f"Must be one of: {', '.join(sorted(VALID_TYPES))}",
        )

    booking = db.query(TransportBooking).filter(TransportBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Transport booking not found")

    booking.type = request.type
    booking.operator = request.operator
    booking.service_number = request.service_number
    booking.departure_station = request.departure_station
    booking.arrival_station = request.arrival_station
    booking.departure_datetime = request.departure_datetime
    booking.arrival_datetime = request.arrival_datetime
    booking.carriage = request.carriage
    booking.seat = request.seat
    booking.notes = request.notes

    if request.booking_reference:
        booking.booking_reference_encrypted = encrypt(request.booking_reference)
        booking.booking_reference_masked = mask_value(request.booking_reference, reveal=1)
    else:
        booking.booking_reference_encrypted = None
        booking.booking_reference_masked = None

    db.commit()
    db.refresh(booking)
    return _booking_to_data(booking, vault_open)


@router.delete("/transport-bookings/{booking_id}", status_code=204)
def delete_transport_booking(
    booking_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a transport booking and its document from storage."""
    booking = db.query(TransportBooking).filter(TransportBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Transport booking not found")

    if booking.document_path:
        try:
            from ..vault_storage import get_vault_storage

            storage = get_vault_storage()
            storage.delete(booking.document_path)
        except Exception:
            log.warning("Failed to delete document for booking %s", booking_id, exc_info=True)

    db.delete(booking)
    db.commit()


@router.post("/transport-bookings/{booking_id}/document", status_code=200)
async def upload_transport_document(
    booking_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> TransportBookingData:
    """Upload a document (PDF/image) for a transport booking."""
    from ..vault_storage import get_vault_storage

    booking = db.query(TransportBooking).filter(TransportBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Transport booking not found")

    content_type = file.content_type or ""
    if content_type not in DOC_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Use PDF, JPEG, PNG, or WebP.",
        )

    content = await file.read()
    if len(content) > MAX_DOC_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    storage = get_vault_storage()

    # Delete old document if exists
    if booking.document_path:
        try:
            storage.delete(booking.document_path)
        except Exception:
            log.warning(
                "Failed to delete old document for booking %s",
                booking_id,
                exc_info=True,
            )

    key = storage.save(admin.id, file.filename or "document", content, content_type)
    booking.document_path = key
    booking.document_name = file.filename
    booking.document_mime_type = content_type
    booking.document_size = len(content)
    db.commit()
    db.refresh(booking)
    return _booking_to_data(booking)


@router.get("/transport-bookings/{booking_id}/document")
def get_transport_document(
    booking_id: int,
    viewer: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> Response:
    """Stream transport booking document content through the backend."""
    from ..vault_storage import get_vault_storage

    booking = db.query(TransportBooking).filter(TransportBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Transport booking not found")
    if not booking.document_path:
        raise HTTPException(status_code=404, detail="No document attached")

    storage = get_vault_storage()
    content = storage.read(booking.document_path)
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found in storage")
    return Response(
        content=content, media_type=booking.document_mime_type or "application/octet-stream"
    )


@router.delete("/transport-bookings/{booking_id}/document", status_code=204)
def delete_transport_document(
    booking_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete the document from a transport booking."""
    from ..vault_storage import get_vault_storage

    booking = db.query(TransportBooking).filter(TransportBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Transport booking not found")
    if not booking.document_path:
        raise HTTPException(status_code=404, detail="No document attached")

    storage = get_vault_storage()
    storage.delete(booking.document_path)
    booking.document_path = None
    booking.document_name = None
    booking.document_mime_type = None
    booking.document_size = None
    db.commit()
