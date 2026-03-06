"""Admin endpoints for meme curation."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth.session import get_admin_user
from ..database import get_db
from ..log_config import get_logger
from ..models import Meme, User
from ..storage import get_storage
from ..telegram.meme_processing import IMAGE_MIME_TYPES, process_meme

log = get_logger(__name__)

router = APIRouter(prefix="/memes", tags=["admin-memes"])


# --- Response models ---


class MemeResponse(BaseModel):
    id: int
    status: str
    source_type: str
    source_url: str | None
    media_path: str
    mime_type: str
    width: int | None
    height: int | None
    language: str | None
    category: str | None
    description_en: str | None
    is_site_worthy: bool | None
    telegram_message_id: int | None
    created_at: str
    approved_at: str | None


class MemeListResponse(BaseModel):
    memes: list[MemeResponse]
    total: int


class MemeStatsResponse(BaseModel):
    pending: int
    approved: int
    rejected: int
    total: int


class MemeUpdateRequest(BaseModel):
    language: str | None = None
    category: str | None = None
    description_en: str | None = None
    is_site_worthy: bool | None = None


class MemeApproveRequest(BaseModel):
    language: str | None = None
    category: str | None = None
    description_en: str | None = None


# --- Helpers ---


def _meme_to_response(m: Meme) -> MemeResponse:
    return MemeResponse(
        id=m.id,
        status=m.status,
        source_type=m.source_type,
        source_url=m.source_url,
        media_path=m.media_path,
        mime_type=m.mime_type,
        width=m.width,
        height=m.height,
        language=m.language,
        category=m.category,
        description_en=m.description_en,
        is_site_worthy=m.is_site_worthy,
        telegram_message_id=m.telegram_message_id,
        created_at=m.created_at.isoformat(),
        approved_at=m.approved_at.isoformat() if m.approved_at else None,
    )


# --- Endpoints ---


@router.get("/stats", response_model=MemeStatsResponse)
def meme_stats(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> MemeStatsResponse:
    """Get meme counts by status."""
    rows = (
        db.query(Meme.status, func.count(Meme.id))
        .filter(Meme.is_test == False)  # noqa: E712
        .group_by(Meme.status)
        .all()
    )
    counts: dict[str, int] = {status: count for status, count in rows}
    return MemeStatsResponse(
        pending=counts.get("pending", 0),
        approved=counts.get("approved", 0),
        rejected=counts.get("rejected", 0),
        total=sum(counts.values()),
    )


@router.get("", response_model=MemeListResponse)
def list_memes(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    status: str | None = "pending",
    limit: int = 50,
    offset: int = 0,
) -> MemeListResponse:
    """List memes, optionally filtered by status."""
    query = db.query(Meme).filter(Meme.is_test == False)  # noqa: E712
    if status:
        query = query.filter(Meme.status == status)
    total = query.count()
    memes = query.order_by(Meme.created_at.desc()).offset(offset).limit(limit).all()
    return MemeListResponse(
        memes=[_meme_to_response(m) for m in memes],
        total=total,
    )


@router.post("/upload", response_model=MemeResponse)
async def upload_meme(
    file: Annotated[UploadFile, File()],
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    source_url: str | None = Form(None),
    x_test_mode: Annotated[str | None, Header()] = None,
) -> MemeResponse:
    """Upload a meme image directly (bypasses Telegram)."""
    if not file.content_type or file.content_type not in IMAGE_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    is_test = x_test_mode == "true"

    # Build minimal message dict (message_id=0 skips Telegram dedup)
    message: dict[str, Any] = {"message_id": 0}
    if source_url:
        message["caption"] = source_url

    process_meme(content, file.content_type, message, db, is_test=is_test)

    # Find the just-created meme (most recent)
    meme = db.query(Meme).order_by(Meme.id.desc()).first()
    if not meme:
        raise HTTPException(status_code=500, detail="Meme creation failed")

    # Mark as upload source
    meme.source_type = "upload"
    db.commit()
    db.refresh(meme)

    return _meme_to_response(meme)


@router.get("/{meme_id}", response_model=MemeResponse)
def get_meme(
    meme_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> MemeResponse:
    """Get a single meme by ID."""
    meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    return _meme_to_response(meme)


@router.post("/{meme_id}/approve", response_model=MemeResponse)
def approve_meme(
    meme_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    data: MemeApproveRequest | None = None,
) -> MemeResponse:
    """Approve a meme, optionally updating metadata."""
    meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    meme.status = "approved"
    meme.approved_at = datetime.now(UTC)
    if data:
        if data.language is not None:
            meme.language = data.language
        if data.category is not None:
            meme.category = data.category
        if data.description_en is not None:
            meme.description_en = data.description_en
    db.commit()
    db.refresh(meme)
    log.info("Meme %d approved", meme.id)
    return _meme_to_response(meme)


@router.post("/{meme_id}/reject", response_model=MemeResponse)
def reject_meme(
    meme_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> MemeResponse:
    """Reject a meme."""
    meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    meme.status = "rejected"
    db.commit()
    db.refresh(meme)
    log.info("Meme %d rejected", meme.id)
    return _meme_to_response(meme)


@router.put("/{meme_id}", response_model=MemeResponse)
def update_meme(
    meme_id: int,
    data: MemeUpdateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> MemeResponse:
    """Edit meme metadata."""
    meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    if data.language is not None:
        meme.language = data.language
    if data.category is not None:
        meme.category = data.category
    if data.description_en is not None:
        meme.description_en = data.description_en
    if data.is_site_worthy is not None:
        meme.is_site_worthy = data.is_site_worthy
    db.commit()
    db.refresh(meme)
    log.info("Meme %d updated", meme.id)
    return _meme_to_response(meme)


@router.get("/{meme_id}/media")
def get_meme_media(
    meme_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> Response:
    """Serve meme image (proxy from storage)."""
    meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")

    storage = get_storage("memes")

    # Extract filename from media_path
    # media_path can be a full URL or a local path — extract the filename
    filename = meme.media_path.rsplit("/", 1)[-1]

    if not storage.exists(filename):
        raise HTTPException(status_code=404, detail="Media file not found")

    # For local storage, read from disk
    from pathlib import Path

    if "/" in meme.media_path and not meme.media_path.startswith("http"):
        path = Path(meme.media_path)
        if path.exists():
            return Response(content=path.read_bytes(), media_type=meme.mime_type)

    # For GCS, redirect to the public URL
    return Response(
        status_code=302,
        headers={"Location": storage.get_public_url(filename)},
    )


@router.delete("/test-data", status_code=200)
def delete_test_memes(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Delete all memes marked as test data."""
    count = (
        db.query(Meme)
        .filter(Meme.is_test == True)  # noqa: E712
        .delete()
    )
    db.commit()
    return {"deleted": count}
