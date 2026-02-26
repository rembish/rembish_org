import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user, get_trips_viewer, get_vault_user
from ..database import get_db
from ..models import (
    TCCDestination,
    Trip,
    TripDestination,
    TripDocument,
    User,
)
from .models import (
    PassportInfo,
    TripDocumentData,
    TripDocumentsTabResponse,
    TripTravelDocInfo,
)
from .trips_country_info import get_trip_travel_docs, get_trip_vaccination_needs

log = logging.getLogger(__name__)

router = APIRouter()

DOC_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
MAX_DOC_SIZE = 10 * 1024 * 1024  # 10 MB


def _doc_to_data(doc: TripDocument) -> TripDocumentData:
    return TripDocumentData(
        id=doc.id,
        trip_id=doc.trip_id,
        label=doc.label,
        document_name=doc.document_name,
        document_mime_type=doc.document_mime_type,
        document_size=doc.document_size,
        notes=doc.notes,
        sort_order=doc.sort_order,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
    )


@router.get("/trips/{trip_id}/documents-tab", response_model=TripDocumentsTabResponse)
def get_documents_tab(
    trip_id: int,
    viewer: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> TripDocumentsTabResponse:
    """Combined data for the Documents tab: passport, travel docs, vaccinations, trip documents."""
    trip = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations)
            .joinedload(TripDestination.tcc_destination)
            .joinedload(TCCDestination.un_country),
        )
        .filter(Trip.id == trip_id)
        .first()
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip_end = trip.end_date or trip.start_date

    # Collect trip's destination country codes
    trip_country_codes: set[str] = set()
    for td in trip.destinations:
        un = td.tcc_destination.un_country
        if un:
            trip_country_codes.add(un.iso_alpha2.upper())

    # Travel docs (reuse shared helper, filtered to trip countries)
    travel_docs_by_country = get_trip_travel_docs(trip, trip_id, db)
    travel_docs: list[TripTravelDocInfo] = []
    seen_passport_ids: set[int] = set()
    passports: list[PassportInfo] = []
    for cc, country_docs in sorted(travel_docs_by_country.items()):
        if cc not in trip_country_codes:
            continue
        for vtd in country_docs:
            travel_docs.append(
                TripTravelDocInfo(
                    id=vtd.id,
                    doc_type=vtd.doc_type,
                    label=vtd.label,
                    valid_until=vtd.valid_until.isoformat() if vtd.valid_until else None,
                    entry_type=vtd.entry_type,
                    passport_label=vtd.passport.label if vtd.passport else None,
                    expires_before_trip=bool(vtd.valid_until and vtd.valid_until < trip_end),
                    has_files=len(vtd.files) > 0 if vtd.files else False,
                )
            )
            # Collect passports referenced by matched visas
            if vtd.passport and vtd.passport.id not in seen_passport_ids:
                seen_passport_ids.add(vtd.passport.id)
                passports.append(
                    PassportInfo(
                        id=vtd.passport.id,
                        label=vtd.passport.label,
                        issuing_country=vtd.passport.issuing_country,
                        expiry_date=(
                            vtd.passport.expiry_date.isoformat()
                            if vtd.passport.expiry_date
                            else None
                        ),
                        has_files=len(vtd.passport.files) > 0 if vtd.passport.files else False,
                    )
                )

    # Required vaccines (for ICV / vaccination book reminder)
    vax_tuples = get_trip_vaccination_needs(trip, db, viewer.id)
    required_vaccines = [name for name, priority, _covered in vax_tuples if priority == "required"]

    # Trip documents
    docs = (
        db.query(TripDocument)
        .filter(TripDocument.trip_id == trip_id)
        .order_by(TripDocument.sort_order, TripDocument.created_at)
        .all()
    )

    return TripDocumentsTabResponse(
        passports=passports,
        travel_docs=travel_docs,
        required_vaccines=required_vaccines,
        documents=[_doc_to_data(d) for d in docs],
    )


@router.post("/trips/{trip_id}/documents", response_model=TripDocumentData)
async def upload_trip_document(
    trip_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    label: str = Form(...),
    notes: str | None = Form(None),
) -> TripDocumentData:
    """Upload a file and create a trip document record."""
    from ..vault_storage import get_vault_storage

    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

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
    key = storage.save(admin.id, file.filename or "document", content, content_type)

    # Determine next sort_order
    max_order = (
        db.query(TripDocument.sort_order)
        .filter(TripDocument.trip_id == trip_id)
        .order_by(TripDocument.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order else 0

    doc = TripDocument(
        trip_id=trip_id,
        label=label.strip(),
        document_path=key,
        document_name=file.filename,
        document_mime_type=content_type,
        document_size=len(content),
        notes=notes.strip() if notes else None,
        sort_order=next_order,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _doc_to_data(doc)


@router.put("/trips/{trip_id}/documents/{doc_id}", response_model=TripDocumentData)
def update_trip_document(
    trip_id: int,
    doc_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    label: str = Form(...),
    notes: str | None = Form(None),
) -> TripDocumentData:
    """Update label/notes on a trip document."""
    doc = (
        db.query(TripDocument)
        .filter(TripDocument.id == doc_id, TripDocument.trip_id == trip_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.label = label.strip()
    doc.notes = notes.strip() if notes else None
    db.commit()
    db.refresh(doc)
    return _doc_to_data(doc)


@router.delete("/trips/{trip_id}/documents/{doc_id}", status_code=204)
def delete_trip_document(
    trip_id: int,
    doc_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a trip document and its file from storage."""
    doc = (
        db.query(TripDocument)
        .filter(TripDocument.id == doc_id, TripDocument.trip_id == trip_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.document_path:
        try:
            from ..vault_storage import get_vault_storage

            storage = get_vault_storage()
            storage.delete(doc.document_path)
        except Exception:
            log.warning("Failed to delete file for trip document %s", doc_id, exc_info=True)

    db.delete(doc)
    db.commit()


@router.get("/trips/{trip_id}/documents/{doc_id}/file")
def get_trip_document_file(
    trip_id: int,
    doc_id: int,
    vault_user: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> Response:
    """Download a trip document file (vault must be unlocked)."""
    from ..vault_storage import get_vault_storage

    doc = (
        db.query(TripDocument)
        .filter(TripDocument.id == doc_id, TripDocument.trip_id == trip_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_vault_storage()
    content = storage.read(doc.document_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found in storage")
    return Response(
        content=content,
        media_type=doc.document_mime_type or "application/octet-stream",
    )
