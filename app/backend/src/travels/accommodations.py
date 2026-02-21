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
from ..extraction import extract_accommodation_data
from ..models import Accommodation, Trip, User
from .models import (
    AccommodationCreateRequest,
    AccommodationData,
    AccommodationExtractResponse,
    AccommodationsResponse,
    ExtractedAccommodationResponse,
)

log = logging.getLogger(__name__)

router = APIRouter()

MAX_EXTRACT_SIZE = 10 * 1024 * 1024  # 10 MB
EXTRACT_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
VALID_PLATFORMS = {"booking", "agoda", "airbnb", "direct", "other"}
VALID_PAYMENT_STATUSES = {"paid", "pay_at_property", "pay_by_date"}
DOC_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
MAX_DOC_SIZE = 10 * 1024 * 1024  # 10 MB


def _confirmation_display(acc: Accommodation, vault_open: bool) -> str | None:
    """Return decrypted confirmation code if vault is unlocked, masked otherwise."""
    if not acc.confirmation_code_encrypted and not acc.confirmation_code_masked:
        return None
    if acc.confirmation_code_encrypted:
        try:
            plaintext = decrypt(acc.confirmation_code_encrypted)
            return plaintext if vault_open else mask_value(plaintext, reveal=1)
        except Exception:
            pass
    return acc.confirmation_code_masked


def _acc_to_data(acc: Accommodation, vault_open: bool = False) -> AccommodationData:
    return AccommodationData(
        id=acc.id,
        trip_id=acc.trip_id,
        property_name=acc.property_name,
        platform=acc.platform,
        checkin_date=acc.checkin_date,
        checkout_date=acc.checkout_date,
        address=acc.address,
        total_amount=acc.total_amount,
        payment_status=acc.payment_status,
        payment_date=acc.payment_date,
        guests=acc.guests,
        rooms=acc.rooms,
        confirmation_code=_confirmation_display(acc, vault_open),
        booking_url=acc.booking_url,
        has_document=acc.document_path is not None,
        document_name=acc.document_name,
        document_mime_type=acc.document_mime_type,
        document_size=acc.document_size,
        notes=acc.notes,
    )


@router.post(
    "/trips/{trip_id}/accommodations/extract",
    response_model=AccommodationExtractResponse,
)
async def extract_accommodation(
    trip_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> AccommodationExtractResponse:
    """Upload an accommodation booking PDF/image and extract data via AI."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    content_type = file.content_type or ""
    if content_type not in EXTRACT_MIME_TYPES:
        return AccommodationExtractResponse(
            error=f"Unsupported file type: {content_type}. Use PDF or image."
        )

    content = await file.read()
    if len(content) > MAX_EXTRACT_SIZE:
        return AccommodationExtractResponse(error="File too large (max 10 MB)")

    result = extract_accommodation_data(content, content_type)
    if result.error:
        return AccommodationExtractResponse(error=result.error)
    if not result.accommodation:
        return AccommodationExtractResponse(error="No accommodation data extracted")

    # Check for duplicates: same checkin_date + property_name
    is_dup = False
    if result.accommodation.checkin_date and result.accommodation.property_name:
        existing = (
            db.query(Accommodation)
            .filter(
                Accommodation.trip_id == trip_id,
                Accommodation.checkin_date == result.accommodation.checkin_date,
                Accommodation.property_name == result.accommodation.property_name,
            )
            .first()
        )
        is_dup = existing is not None

    extracted = ExtractedAccommodationResponse(
        property_name=result.accommodation.property_name,
        platform=result.accommodation.platform,
        checkin_date=result.accommodation.checkin_date,
        checkout_date=result.accommodation.checkout_date,
        address=result.accommodation.address,
        total_amount=result.accommodation.total_amount,
        payment_status=result.accommodation.payment_status,
        payment_date=result.accommodation.payment_date,
        guests=result.accommodation.guests,
        rooms=result.accommodation.rooms,
        confirmation_code=result.accommodation.confirmation_code,
        notes=result.accommodation.notes,
        is_duplicate=is_dup,
    )

    return AccommodationExtractResponse(accommodation=extracted)


@router.get(
    "/trips/{trip_id}/accommodations",
    response_model=AccommodationsResponse,
)
def get_trip_accommodations(
    trip_id: int,
    viewer: Annotated[User, Depends(get_trips_viewer)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked_for_viewer)],
    db: Session = Depends(get_db),
) -> AccommodationsResponse:
    """Get all accommodations for a trip, ordered by check-in date."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    accs = (
        db.query(Accommodation)
        .filter(Accommodation.trip_id == trip_id)
        .order_by(Accommodation.checkin_date)
        .all()
    )

    return AccommodationsResponse(accommodations=[_acc_to_data(a, vault_open) for a in accs])


@router.post(
    "/trips/{trip_id}/accommodations",
    response_model=AccommodationData,
)
def create_accommodation(
    trip_id: int,
    request: AccommodationCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked)],
    db: Session = Depends(get_db),
) -> AccommodationData:
    """Create an accommodation for a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if request.platform and request.platform not in VALID_PLATFORMS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid platform: {request.platform}. "
            f"Must be one of: {', '.join(sorted(VALID_PLATFORMS))}",
        )

    if request.payment_status and request.payment_status not in VALID_PAYMENT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid payment_status: {request.payment_status}. "
            f"Must be one of: {', '.join(sorted(VALID_PAYMENT_STATUSES))}",
        )

    acc = Accommodation(
        trip_id=trip_id,
        property_name=request.property_name,
        platform=request.platform,
        checkin_date=request.checkin_date,
        checkout_date=request.checkout_date,
        address=request.address,
        total_amount=request.total_amount,
        payment_status=request.payment_status,
        payment_date=request.payment_date,
        guests=request.guests,
        rooms=request.rooms,
        booking_url=request.booking_url,
        notes=request.notes,
    )
    if request.confirmation_code:
        acc.confirmation_code_encrypted = encrypt(request.confirmation_code)
        acc.confirmation_code_masked = mask_value(request.confirmation_code, reveal=1)
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return _acc_to_data(acc, vault_open)


@router.put("/accommodations/{accommodation_id}", response_model=AccommodationData)
def update_accommodation(
    accommodation_id: int,
    request: AccommodationCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    vault_open: Annotated[bool, Depends(is_vault_unlocked)],
    db: Session = Depends(get_db),
) -> AccommodationData:
    """Update an accommodation."""
    acc = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accommodation not found")

    if request.platform and request.platform not in VALID_PLATFORMS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid platform: {request.platform}. "
            f"Must be one of: {', '.join(sorted(VALID_PLATFORMS))}",
        )

    if request.payment_status and request.payment_status not in VALID_PAYMENT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid payment_status: {request.payment_status}. "
            f"Must be one of: {', '.join(sorted(VALID_PAYMENT_STATUSES))}",
        )

    acc.property_name = request.property_name
    acc.platform = request.platform
    acc.checkin_date = request.checkin_date
    acc.checkout_date = request.checkout_date
    acc.address = request.address
    acc.total_amount = request.total_amount
    acc.payment_status = request.payment_status
    acc.payment_date = request.payment_date
    acc.guests = request.guests
    acc.rooms = request.rooms
    acc.booking_url = request.booking_url
    acc.notes = request.notes

    if request.confirmation_code:
        acc.confirmation_code_encrypted = encrypt(request.confirmation_code)
        acc.confirmation_code_masked = mask_value(request.confirmation_code, reveal=1)
    else:
        acc.confirmation_code_encrypted = None
        acc.confirmation_code_masked = None

    db.commit()
    db.refresh(acc)
    return _acc_to_data(acc, vault_open)


@router.delete("/accommodations/{accommodation_id}", status_code=204)
def delete_accommodation(
    accommodation_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete an accommodation and its document from storage."""
    acc = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accommodation not found")

    if acc.document_path:
        try:
            from ..vault_storage import get_vault_storage

            storage = get_vault_storage()
            storage.delete(acc.document_path)
        except Exception:
            log.warning(
                "Failed to delete document for accommodation %s",
                accommodation_id,
                exc_info=True,
            )

    db.delete(acc)
    db.commit()


@router.post("/accommodations/{accommodation_id}/document", status_code=200)
async def upload_accommodation_document(
    accommodation_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> AccommodationData:
    """Upload a document (PDF/image) for an accommodation."""
    from ..vault_storage import get_vault_storage

    acc = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accommodation not found")

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
    if acc.document_path:
        try:
            storage.delete(acc.document_path)
        except Exception:
            log.warning(
                "Failed to delete old document for accommodation %s",
                accommodation_id,
                exc_info=True,
            )

    key = storage.save(admin.id, file.filename or "document", content, content_type)
    acc.document_path = key
    acc.document_name = file.filename
    acc.document_mime_type = content_type
    acc.document_size = len(content)
    db.commit()
    db.refresh(acc)
    return _acc_to_data(acc)


@router.get("/accommodations/{accommodation_id}/document")
def get_accommodation_document_url(
    accommodation_id: int,
    viewer: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Get a signed URL for the accommodation's document."""
    from ..vault_storage import get_vault_storage

    acc = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    if not acc.document_path:
        raise HTTPException(status_code=404, detail="No document attached")

    storage = get_vault_storage()
    url = storage.get_signed_url(acc.document_path)
    return {"url": url}


@router.delete("/accommodations/{accommodation_id}/document", status_code=204)
def delete_accommodation_document(
    accommodation_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete the document from an accommodation."""
    from ..vault_storage import get_vault_storage

    acc = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    if not acc.document_path:
        raise HTTPException(status_code=404, detail="No document attached")

    storage = get_vault_storage()
    storage.delete(acc.document_path)
    acc.document_path = None
    acc.document_name = None
    acc.document_mime_type = None
    acc.document_size = None
    db.commit()
