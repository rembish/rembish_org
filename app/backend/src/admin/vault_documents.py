from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_vault_user
from ..crypto import encrypt, mask_value
from ..database import get_db
from ..log_config import get_logger
from ..models import User, VaultDocument
from .vault_models import (
    DocumentListResponse,
    DocumentRequest,
    DocumentResponse,
    _clean_number,
    _doc_to_response,
)

log = get_logger(__name__)
router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
    user_id: int | None = None,
) -> DocumentListResponse:
    """List vault documents, optionally filtered by user_id."""
    query = db.query(VaultDocument).options(joinedload(VaultDocument.files))
    if user_id is not None:
        query = query.filter(VaultDocument.user_id == user_id)
    query = query.order_by(VaultDocument.label)
    docs = query.all()
    return DocumentListResponse(documents=[_doc_to_response(d) for d in docs])


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    data: DocumentRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Create a vault document with encrypted fields."""
    doc = VaultDocument(
        user_id=data.user_id,
        doc_type=data.doc_type,
        label=data.label,
        proper_name=data.proper_name,
        issuing_country=data.issuing_country,
        issue_date=data.issue_date,
        expiry_date=data.expiry_date,
    )
    clean_num = _clean_number(data.number)
    if clean_num:
        doc.number_encrypted = encrypt(clean_num)
        doc.number_masked = mask_value(clean_num)
    if data.notes:
        doc.notes_encrypted = encrypt(data.notes)
        doc.notes_masked = mask_value(data.notes)

    db.add(doc)
    db.commit()
    db.refresh(doc)
    log.info(f"Created vault document: {doc.label} for user_id={doc.user_id}")
    return _doc_to_response(doc)


@router.put("/documents/{doc_id}", response_model=DocumentResponse)
def update_document(
    doc_id: int,
    data: DocumentRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Update a vault document (re-encrypts sensitive fields)."""
    doc = db.query(VaultDocument).filter(VaultDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc.user_id = data.user_id
    doc.doc_type = data.doc_type
    doc.label = data.label
    doc.proper_name = data.proper_name
    doc.issuing_country = data.issuing_country
    doc.issue_date = data.issue_date
    doc.expiry_date = data.expiry_date

    clean_num = _clean_number(data.number)
    if clean_num:
        doc.number_encrypted = encrypt(clean_num)
        doc.number_masked = mask_value(clean_num)
    else:
        doc.number_encrypted = None
        doc.number_masked = None

    if data.notes:
        doc.notes_encrypted = encrypt(data.notes)
        doc.notes_masked = mask_value(data.notes)
    else:
        doc.notes_encrypted = None
        doc.notes_masked = None

    db.commit()
    db.refresh(doc)
    log.info(f"Updated vault document: {doc.label}")
    return _doc_to_response(doc)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> None:
    """Archive a vault document (soft-delete)."""
    doc = db.query(VaultDocument).filter(VaultDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    log.info(f"Archiving vault document: {doc.label}")
    doc.is_archived = True
    db.commit()


@router.post("/documents/{doc_id}/restore", response_model=DocumentResponse)
def restore_document(
    doc_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Restore an archived vault document."""
    doc = db.query(VaultDocument).filter(VaultDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    doc.is_archived = False
    db.commit()
    db.refresh(doc)
    log.info(f"Restored vault document: {doc.label}")
    return _doc_to_response(doc)
