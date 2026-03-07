"""Admin CRUD for cosplay costumes and photo uploads."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.session import get_admin_user
from ..database import get_db
from ..log_config import get_logger
from ..models import CosplayCostume, CosplayPhoto, User
from ..storage import get_storage

log = get_logger(__name__)

router = APIRouter(prefix="/cosplay", tags=["admin-cosplay"])

IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


# --- Response models ---


class CosplayPhotoResponse(BaseModel):
    id: int
    filename: str
    width: int | None
    height: int | None
    sort_order: int


class CosplayCostumeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    sort_order: int
    cover_photo_id: int | None
    photos: list[CosplayPhotoResponse]


class CosplayCostumeCreateRequest(BaseModel):
    name: str
    description: str | None = None
    sort_order: int = 0


class CosplayPhotoReorderRequest(BaseModel):
    photo_ids: list[int]


# --- Helpers ---


def _costume_to_response(c: CosplayCostume) -> CosplayCostumeResponse:
    return CosplayCostumeResponse(
        id=c.id,
        name=c.name,
        description=c.description,
        sort_order=c.sort_order,
        cover_photo_id=c.cover_photo_id,
        photos=[
            CosplayPhotoResponse(
                id=p.id,
                filename=p.filename,
                width=p.width,
                height=p.height,
                sort_order=p.sort_order,
            )
            for p in c.photos
        ],
    )


# --- Endpoints ---


@router.get("", response_model=list[CosplayCostumeResponse])
def list_costumes(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> list[CosplayCostumeResponse]:
    """List all costumes with photos."""
    costumes = db.query(CosplayCostume).order_by(CosplayCostume.sort_order).all()
    return [_costume_to_response(c) for c in costumes]


@router.post("", response_model=CosplayCostumeResponse)
def create_costume(
    body: CosplayCostumeCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> CosplayCostumeResponse:
    """Create a new costume."""
    c = CosplayCostume(name=body.name, description=body.description, sort_order=body.sort_order)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _costume_to_response(c)


@router.put("/{costume_id}", response_model=CosplayCostumeResponse)
def update_costume(
    costume_id: int,
    body: CosplayCostumeCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> CosplayCostumeResponse:
    """Update a costume."""
    c = db.query(CosplayCostume).filter(CosplayCostume.id == costume_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Costume not found")
    c.name = body.name
    c.description = body.description
    c.sort_order = body.sort_order
    db.commit()
    db.refresh(c)
    return _costume_to_response(c)


@router.delete("/{costume_id}", status_code=204)
def delete_costume(
    costume_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a costume and all its photos."""
    c = db.query(CosplayCostume).filter(CosplayCostume.id == costume_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Costume not found")
    db.delete(c)
    db.commit()


@router.post("/{costume_id}/photos", response_model=CosplayPhotoResponse)
async def upload_photo(
    costume_id: int,
    file: Annotated[UploadFile, File()],
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> CosplayPhotoResponse:
    """Upload a photo to a costume."""
    c = db.query(CosplayCostume).filter(CosplayCostume.id == costume_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Costume not found")
    if not file.content_type or file.content_type not in IMAGE_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Get dimensions
    import io

    width, height = None, None
    try:
        img = Image.open(io.BytesIO(content))
        width, height = img.size
    except Exception:
        pass

    # Save to storage
    ext = (
        file.filename.rsplit(".", 1)[-1].lower()
        if file.filename and "." in file.filename
        else "jpg"
    )
    filename = f"{uuid.uuid4().hex}.{ext}"
    storage = get_storage("cosplay")
    storage.save(filename, content, file.content_type)

    # Next sort_order
    max_order = (
        db.query(CosplayPhoto)
        .filter(CosplayPhoto.costume_id == costume_id)
        .order_by(CosplayPhoto.sort_order.desc())
        .first()
    )
    next_order = (max_order.sort_order + 1) if max_order else 0

    photo = CosplayPhoto(
        costume_id=costume_id,
        filename=filename,
        width=width,
        height=height,
        sort_order=next_order,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    log.info("Cosplay photo uploaded: costume=%s, file=%s", c.name, filename)
    return CosplayPhotoResponse(
        id=photo.id,
        filename=photo.filename,
        width=photo.width,
        height=photo.height,
        sort_order=photo.sort_order,
    )


@router.put("/{costume_id}/photos/reorder")
def reorder_photos(
    costume_id: int,
    body: CosplayPhotoReorderRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Reorder photos within a costume."""
    c = db.query(CosplayCostume).filter(CosplayCostume.id == costume_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Costume not found")
    for idx, photo_id in enumerate(body.photo_ids):
        db.query(CosplayPhoto).filter(
            CosplayPhoto.id == photo_id, CosplayPhoto.costume_id == costume_id
        ).update({CosplayPhoto.sort_order: idx})
    db.commit()
    return {"status": "ok"}


@router.put("/{costume_id}/cover/{photo_id}")
def set_cover_photo(
    costume_id: int,
    photo_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Set a photo as the costume cover."""
    c = db.query(CosplayCostume).filter(CosplayCostume.id == costume_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Costume not found")
    photo = (
        db.query(CosplayPhoto)
        .filter(CosplayPhoto.id == photo_id, CosplayPhoto.costume_id == costume_id)
        .first()
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    c.cover_photo_id = photo_id
    db.commit()
    return {"status": "ok"}


@router.delete("/{costume_id}/photos/{photo_id}", status_code=204)
def delete_photo(
    costume_id: int,
    photo_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a photo from a costume."""
    photo = (
        db.query(CosplayPhoto)
        .filter(CosplayPhoto.id == photo_id, CosplayPhoto.costume_id == costume_id)
        .first()
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db.delete(photo)
    db.commit()
