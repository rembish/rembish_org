"""Public cosplay gallery endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CosplayCostume, CosplayPhoto
from ..storage import get_storage

router = APIRouter(prefix="/cosplay", tags=["cosplay"])


class PublicCosplayPhoto(BaseModel):
    id: int
    filename: str
    width: int | None
    height: int | None


class PublicCosplayCostume(BaseModel):
    id: int
    name: str
    description: str | None
    cover_photo_id: int | None
    photos: list[PublicCosplayPhoto]


@router.get("", response_model=list[PublicCosplayCostume])
def list_cosplay_costumes(
    db: Session = Depends(get_db),
) -> list[PublicCosplayCostume]:
    """List all costumes with photos (public, no auth)."""
    costumes = db.query(CosplayCostume).order_by(CosplayCostume.sort_order).all()
    return [
        PublicCosplayCostume(
            id=c.id,
            name=c.name,
            description=c.description,
            cover_photo_id=c.cover_photo_id,
            photos=[
                PublicCosplayPhoto(
                    id=p.id,
                    filename=p.filename,
                    width=p.width,
                    height=p.height,
                )
                for p in c.photos
            ],
        )
        for c in costumes
    ]


@router.get("/photos/{photo_id}", response_model=None)
def get_cosplay_photo(
    photo_id: int,
    db: Session = Depends(get_db),
) -> FileResponse | RedirectResponse:
    """Serve a cosplay photo file (public)."""
    photo = db.query(CosplayPhoto).filter(CosplayPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    storage = get_storage("cosplay")
    url = storage.get_public_url(photo.filename)

    # GCS: redirect to public URL
    if url.startswith("http"):
        return RedirectResponse(url=url, status_code=302)

    # Local dev: serve file directly
    path = Path(url)
    if not path.exists():
        docker_path = Path("/app/data/cosplay") / photo.filename
        if docker_path.exists():
            path = docker_path
        else:
            raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path, media_type="image/jpeg")
