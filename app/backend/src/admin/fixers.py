from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session, subqueryload

from ..auth.session import get_admin_user, get_trips_viewer
from ..database import get_db
from ..log_config import get_logger
from ..models import UNCountry, User
from ..models.fixer import Fixer, FixerCountry

log = get_logger(__name__)
router = APIRouter(prefix="/fixers", tags=["fixers"])


class FixerLinkItem(BaseModel):
    type: str
    url: str


class FixerRequest(BaseModel):
    name: str
    type: Literal["guide", "fixer", "driver", "coordinator", "agency"]
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    notes: str | None = None
    rating: int | None = None
    links: list[FixerLinkItem] = []
    country_codes: list[str] = []


class FixerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    phone: str | None
    whatsapp: str | None
    email: str | None
    notes: str | None
    rating: int | None
    links: list[FixerLinkItem]
    country_codes: list[str]


class FixerListResponse(BaseModel):
    fixers: list[FixerResponse]


class CountryOption(BaseModel):
    code: str
    name: str


class CountryOptionsResponse(BaseModel):
    countries: list[CountryOption]


def _fixer_to_response(fixer: Fixer) -> FixerResponse:
    return FixerResponse(
        id=fixer.id,
        name=fixer.name,
        type=fixer.type,
        phone=fixer.phone,
        whatsapp=fixer.whatsapp,
        email=fixer.email,
        notes=fixer.notes,
        rating=fixer.rating,
        links=[FixerLinkItem(**lnk) for lnk in (fixer.links or [])],
        country_codes=sorted(c.country_code for c in fixer.countries),
    )


@router.get("/countries", response_model=CountryOptionsResponse)
def list_countries(
    viewer: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> CountryOptionsResponse:
    """Return all UN countries as {code, name} pairs sorted by name."""
    rows = db.query(UNCountry.iso_alpha2, UNCountry.name).order_by(UNCountry.name).all()
    return CountryOptionsResponse(
        countries=[CountryOption(code=r.iso_alpha2, name=r.name) for r in rows],
    )


@router.get("/", response_model=FixerListResponse)
def list_fixers(
    viewer: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
    country: str | None = None,
    search: str | None = None,
) -> FixerListResponse:
    """List all fixers, optionally filtered by country or name search."""
    query = db.query(Fixer).options(subqueryload(Fixer.countries))

    if country:
        query = query.join(Fixer.countries).filter(FixerCountry.country_code == country.upper()[:2])

    if search:
        pattern = f"%{search}%"
        query = query.filter(Fixer.name.ilike(pattern))

    query = query.order_by(Fixer.name)
    fixers = query.all()
    return FixerListResponse(fixers=[_fixer_to_response(f) for f in fixers])


@router.post(
    "/",
    response_model=FixerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fixer(
    data: FixerRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> FixerResponse:
    """Create a new fixer contact."""
    if data.rating is not None and not (1 <= data.rating <= 4):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Rating must be between 1 and 4",
        )

    fixer = Fixer(
        name=data.name,
        type=data.type,
        phone=data.phone or None,
        whatsapp=data.whatsapp or None,
        email=data.email or None,
        notes=data.notes or None,
        rating=data.rating,
        links=[lnk.model_dump() for lnk in data.links if lnk.url.strip()],
    )
    for code in data.country_codes:
        fixer.countries.append(FixerCountry(country_code=code.upper()[:2]))

    db.add(fixer)
    db.commit()
    db.refresh(fixer)
    log.info(f"Created fixer: {fixer.name}")
    return _fixer_to_response(fixer)


@router.put("/{fixer_id}", response_model=FixerResponse)
def update_fixer(
    fixer_id: int,
    data: FixerRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> FixerResponse:
    """Update an existing fixer contact."""
    fixer = (
        db.query(Fixer).options(subqueryload(Fixer.countries)).filter(Fixer.id == fixer_id).first()
    )
    if not fixer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fixer not found")

    if data.rating is not None and not (1 <= data.rating <= 4):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Rating must be between 1 and 4",
        )

    fixer.name = data.name
    fixer.type = data.type
    fixer.phone = data.phone or None
    fixer.whatsapp = data.whatsapp or None
    fixer.email = data.email or None
    fixer.notes = data.notes or None
    fixer.rating = data.rating
    fixer.links = [lnk.model_dump() for lnk in data.links if lnk.url.strip()]

    # Replace countries: clear + flush + re-insert
    fixer.countries.clear()
    db.flush()
    for code in data.country_codes:
        fixer.countries.append(FixerCountry(country_code=code.upper()[:2]))

    db.commit()
    db.refresh(fixer)
    log.info(f"Updated fixer: {fixer.name}")
    return _fixer_to_response(fixer)


@router.delete("/{fixer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fixer(
    fixer_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a fixer contact (cascades to countries)."""
    fixer = db.query(Fixer).filter(Fixer.id == fixer_id).first()
    if not fixer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fixer not found")
    log.info(f"Deleting fixer: {fixer.name}")
    db.delete(fixer)
    db.commit()
