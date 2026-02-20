from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_vault_user
from ..crypto import encrypt, mask_value
from ..database import get_db
from ..log_config import get_logger
from ..models import (
    Trip,
    TripTravelDoc,
    User,
    VaultDocument,
    VaultFile,
    VaultTravelDoc,
    VaultVaccination,
)
from ..models.vault import TripPassport
from .vault_addresses import router as addresses_router
from .vault_documents import router as documents_router
from .vault_models import (
    ExtractedMetadataResponse,
    TravelDocListResponse,
    TravelDocRequest,
    TravelDocResponse,
    VaultFileResponse,
    _match_passport,
    _travel_doc_to_response,
)
from .vault_programs import router as programs_router
from .vault_vaccinations import router as vaccinations_router

log = get_logger(__name__)
router = APIRouter(prefix="/vault", tags=["admin-vault"])
router.include_router(documents_router)
router.include_router(programs_router)
router.include_router(addresses_router)
router.include_router(vaccinations_router)

# --- Allowed file types & size ---

ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# --- File upload/download endpoints ---


@router.post("/files/upload", response_model=VaultFileResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    label: str | None = Form(None),
) -> VaultFileResponse:
    """Upload a file and attach it to a vault entity."""
    from ..vault_storage import get_vault_storage

    if entity_type not in ("document", "vaccination", "travel_doc"):
        raise HTTPException(status_code=400, detail="Invalid entity_type")

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {mime}")

    # Validate entity exists
    if entity_type == "document":
        if not db.query(VaultDocument).filter(VaultDocument.id == entity_id).first():
            raise HTTPException(status_code=404, detail="Document not found")
    elif entity_type == "vaccination":
        if not db.query(VaultVaccination).filter(VaultVaccination.id == entity_id).first():
            raise HTTPException(status_code=404, detail="Vaccination not found")
    elif entity_type == "travel_doc":
        if not db.query(VaultTravelDoc).filter(VaultTravelDoc.id == entity_id).first():
            raise HTTPException(status_code=404, detail="Travel document not found")

    storage = get_vault_storage()
    key = storage.save(admin.id, file.filename or "upload", content, mime)

    # Count existing files for sort_order
    existing_count = (
        db.query(VaultFile)
        .filter(
            getattr(VaultFile, f"{entity_type}_id") == entity_id
            if entity_type != "travel_doc"
            else VaultFile.travel_doc_id == entity_id
        )
        .count()
    )

    vault_file = VaultFile(
        file_path=key,
        mime_type=mime,
        file_size=len(content),
        label=label,
        sort_order=existing_count,
    )
    if entity_type == "document":
        vault_file.document_id = entity_id
    elif entity_type == "vaccination":
        vault_file.vaccination_id = entity_id
    elif entity_type == "travel_doc":
        vault_file.travel_doc_id = entity_id

    db.add(vault_file)
    db.commit()
    db.refresh(vault_file)
    log.info(f"Uploaded vault file: {key} for {entity_type}={entity_id}")
    return VaultFileResponse(
        id=vault_file.id,
        label=vault_file.label,
        mime_type=vault_file.mime_type,
        file_size=vault_file.file_size,
        sort_order=vault_file.sort_order,
    )


@router.get("/files/{file_id}/url")
def get_file_url(
    file_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Get a signed URL for a vault file."""
    from ..vault_storage import get_vault_storage

    vf = db.query(VaultFile).filter(VaultFile.id == file_id).first()
    if not vf:
        raise HTTPException(status_code=404, detail="File not found")
    storage = get_vault_storage()
    url = storage.get_signed_url(vf.file_path)
    return {"url": url}


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a vault file (storage + record)."""
    from ..vault_storage import get_vault_storage

    vf = db.query(VaultFile).filter(VaultFile.id == file_id).first()
    if not vf:
        raise HTTPException(status_code=404, detail="File not found")
    storage = get_vault_storage()
    storage.delete(vf.file_path)
    db.delete(vf)
    db.commit()
    log.info(f"Deleted vault file: {vf.file_path}")


# --- Travel Document endpoints ---


@router.get("/travel-docs", response_model=TravelDocListResponse)
def list_travel_docs(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
    user_id: int | None = None,
) -> TravelDocListResponse:
    """List travel documents, optionally filtered by user_id."""
    query = db.query(VaultTravelDoc).options(
        joinedload(VaultTravelDoc.files),
        joinedload(VaultTravelDoc.trips),
        joinedload(VaultTravelDoc.passport),
    )
    if user_id is not None:
        query = query.filter(VaultTravelDoc.user_id == user_id)
    query = query.order_by(VaultTravelDoc.label)
    docs = query.all()
    return TravelDocListResponse(travel_docs=[_travel_doc_to_response(d) for d in docs])


@router.post(
    "/travel-docs",
    response_model=TravelDocResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_travel_doc(
    data: TravelDocRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> TravelDocResponse:
    """Create a travel document with encrypted fields."""
    td = VaultTravelDoc(
        user_id=data.user_id,
        doc_type=data.doc_type,
        label=data.label,
        document_id=data.document_id,
        country_code=data.country_code,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        entry_type=data.entry_type,
    )
    if data.notes:
        td.notes_encrypted = encrypt(data.notes)
        td.notes_masked = mask_value(data.notes)

    db.add(td)
    db.commit()
    db.refresh(td)
    log.info(f"Created travel doc: {td.label} for user_id={td.user_id}")
    return _travel_doc_to_response(td)


@router.put("/travel-docs/{doc_id}", response_model=TravelDocResponse)
def update_travel_doc(
    doc_id: int,
    data: TravelDocRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> TravelDocResponse:
    """Update a travel document (re-encrypts notes)."""
    td = db.query(VaultTravelDoc).filter(VaultTravelDoc.id == doc_id).first()
    if not td:
        raise HTTPException(status_code=404, detail="Travel document not found")

    td.user_id = data.user_id
    td.doc_type = data.doc_type
    td.label = data.label
    td.document_id = data.document_id
    td.country_code = data.country_code
    td.valid_from = data.valid_from
    td.valid_until = data.valid_until
    td.entry_type = data.entry_type

    if data.notes:
        td.notes_encrypted = encrypt(data.notes)
        td.notes_masked = mask_value(data.notes)
    else:
        td.notes_encrypted = None
        td.notes_masked = None

    db.commit()
    db.refresh(td)
    log.info(f"Updated travel doc: {td.label}")
    return _travel_doc_to_response(td)


@router.delete("/travel-docs/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_travel_doc(
    doc_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a travel document and all attached files."""
    from ..vault_storage import get_vault_storage

    td = (
        db.query(VaultTravelDoc)
        .options(joinedload(VaultTravelDoc.files))
        .filter(VaultTravelDoc.id == doc_id)
        .first()
    )
    if not td:
        raise HTTPException(status_code=404, detail="Travel document not found")

    # Delete files from storage
    storage = get_vault_storage()
    for f in td.files:
        storage.delete(f.file_path)

    log.info(f"Deleting travel doc: {td.label}")
    db.delete(td)
    db.commit()


@router.post("/travel-docs/{doc_id}/mark-used", response_model=TravelDocResponse)
def mark_travel_doc_used(
    doc_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> TravelDocResponse:
    """Mark a travel document as used by setting valid_until to today."""
    td = (
        db.query(VaultTravelDoc)
        .options(
            joinedload(VaultTravelDoc.files),
            joinedload(VaultTravelDoc.trips),
            joinedload(VaultTravelDoc.passport),
        )
        .filter(VaultTravelDoc.id == doc_id)
        .first()
    )
    if not td:
        raise HTTPException(status_code=404, detail="Travel document not found")
    td.valid_until = date.today()
    db.commit()
    db.refresh(td)
    log.info(f"Marked travel doc as used: {td.label}")
    return _travel_doc_to_response(td)


# --- AI Extraction endpoint ---


@router.post("/travel-docs/extract", response_model=ExtractedMetadataResponse)
def extract_travel_doc(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> ExtractedMetadataResponse:
    """Upload a PDF/image and extract metadata with AI (no save)."""
    from ..extraction import extract_document_metadata

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {mime}")

    result = extract_document_metadata(content, mime)
    if result.error:
        return ExtractedMetadataResponse(error=result.error)
    if result.metadata is None:
        return ExtractedMetadataResponse()

    m = result.metadata
    # Try to match extracted passport number against vault passports
    document_id = None
    if m.passport_number:
        document_id = _match_passport(m.passport_number, db)

    return ExtractedMetadataResponse(
        doc_type=m.doc_type,
        label=m.label,
        country_code=m.country_code,
        valid_from=m.valid_from,
        valid_until=m.valid_until,
        entry_type=m.entry_type,
        notes=m.notes,
        document_id=document_id,
    )


# --- Trip-Document association endpoints ---


@router.post(
    "/travel-docs/{doc_id}/trips/{trip_id}",
    status_code=status.HTTP_201_CREATED,
)
def assign_doc_to_trip(
    doc_id: int,
    trip_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Assign a travel document to a trip (idempotent)."""
    if not db.query(Trip).filter(Trip.id == trip_id).first():
        raise HTTPException(status_code=404, detail="Trip not found")
    td = db.query(VaultTravelDoc).filter(VaultTravelDoc.id == doc_id).first()
    if not td:
        raise HTTPException(status_code=404, detail="Travel document not found")

    existing = (
        db.query(TripTravelDoc)
        .filter(TripTravelDoc.trip_id == trip_id, TripTravelDoc.travel_doc_id == doc_id)
        .first()
    )
    if existing:
        return {"message": "Already assigned"}

    db.add(TripTravelDoc(trip_id=trip_id, travel_doc_id=doc_id))
    db.commit()
    log.info(f"Assigned travel doc {doc_id} to trip {trip_id}")
    return {"message": "Assigned"}


@router.delete(
    "/travel-docs/{doc_id}/trips/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_doc_from_trip(
    doc_id: int,
    trip_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> None:
    """Remove a travel document from a trip."""
    link = (
        db.query(TripTravelDoc)
        .filter(TripTravelDoc.trip_id == trip_id, TripTravelDoc.travel_doc_id == doc_id)
        .first()
    )
    if link:
        db.delete(link)
        db.commit()


@router.get("/travel-docs/suggest")
def suggest_travel_docs(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
    country_code: str | None = None,
    trip_id: int | None = None,
) -> TravelDocListResponse:
    """Suggest valid travel docs for a country, excluding already-assigned and expired."""
    today = date.today()
    query = db.query(VaultTravelDoc).options(
        joinedload(VaultTravelDoc.files),
        joinedload(VaultTravelDoc.trips),
        joinedload(VaultTravelDoc.passport),
    )
    if country_code:
        query = query.filter(VaultTravelDoc.country_code == country_code.upper())
    # Exclude expired
    query = query.filter(
        (VaultTravelDoc.valid_until.is_(None)) | (VaultTravelDoc.valid_until >= today)
    )
    docs = query.all()

    # Exclude already assigned to this trip
    if trip_id:
        assigned_ids = {
            r.travel_doc_id
            for r in db.query(TripTravelDoc.travel_doc_id)
            .filter(TripTravelDoc.trip_id == trip_id)
            .all()
        }
        docs = [d for d in docs if d.id not in assigned_ids]

    return TravelDocListResponse(travel_docs=[_travel_doc_to_response(d) for d in docs])


# --- Trip Passport endpoints ---


@router.put("/trips/{trip_id}/passport/{doc_id}")
def assign_passport(
    trip_id: int,
    doc_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Assign a passport to a trip (replaces existing if any)."""
    if not db.query(Trip).filter(Trip.id == trip_id).first():
        raise HTTPException(status_code=404, detail="Trip not found")
    doc = db.query(VaultDocument).filter(VaultDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.doc_type != "passport":
        raise HTTPException(status_code=422, detail="Document is not a passport")

    existing = db.query(TripPassport).filter(TripPassport.trip_id == trip_id).first()
    if existing:
        existing.document_id = doc_id
    else:
        db.add(TripPassport(trip_id=trip_id, document_id=doc_id))
    db.commit()
    log.info(f"Assigned passport {doc_id} to trip {trip_id}")
    return {"message": "Passport assigned"}


@router.delete("/trips/{trip_id}/passport", status_code=status.HTTP_204_NO_CONTENT)
def remove_passport(
    trip_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> None:
    """Remove passport assignment from a trip."""
    existing = db.query(TripPassport).filter(TripPassport.trip_id == trip_id).first()
    if existing:
        db.delete(existing)
        db.commit()
