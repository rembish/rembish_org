from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_vault_user
from ..crypto import encrypt, mask_value
from ..database import get_db
from ..log_config import get_logger
from ..models import User, VaultVaccination
from .vault_models import (
    VaccinationListResponse,
    VaccinationRequest,
    VaccinationResponse,
    _vaccination_to_response,
)

log = get_logger(__name__)
router = APIRouter()


@router.get("/vaccinations", response_model=VaccinationListResponse)
def list_vaccinations(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
    user_id: int | None = None,
) -> VaccinationListResponse:
    """List vaccinations, optionally filtered by user_id."""
    query = db.query(VaultVaccination).options(joinedload(VaultVaccination.files))
    if user_id is not None:
        query = query.filter(VaultVaccination.user_id == user_id)
    query = query.order_by(VaultVaccination.vaccine_name)
    vaxs = query.all()
    return VaccinationListResponse(vaccinations=[_vaccination_to_response(v) for v in vaxs])


@router.post(
    "/vaccinations",
    response_model=VaccinationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vaccination(
    data: VaccinationRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> VaccinationResponse:
    """Create a vaccination record with encrypted fields."""
    vax = VaultVaccination(
        user_id=data.user_id,
        vaccine_name=data.vaccine_name,
        brand_name=data.brand_name,
        dose_type=data.dose_type,
        date_administered=data.date_administered,
        expiry_date=data.expiry_date,
    )
    if data.batch_number:
        vax.batch_number_encrypted = encrypt(data.batch_number)
        vax.batch_number_masked = mask_value(data.batch_number)
    if data.notes:
        vax.notes_encrypted = encrypt(data.notes)
        vax.notes_masked = mask_value(data.notes)

    db.add(vax)
    db.commit()
    db.refresh(vax)
    log.info(f"Created vaccination: {vax.vaccine_name} for user_id={vax.user_id}")
    return _vaccination_to_response(vax)


@router.put("/vaccinations/{vax_id}", response_model=VaccinationResponse)
def update_vaccination(
    vax_id: int,
    data: VaccinationRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> VaccinationResponse:
    """Update a vaccination record (re-encrypts sensitive fields)."""
    vax = db.query(VaultVaccination).filter(VaultVaccination.id == vax_id).first()
    if not vax:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")

    vax.user_id = data.user_id
    vax.vaccine_name = data.vaccine_name
    vax.brand_name = data.brand_name
    vax.dose_type = data.dose_type
    vax.date_administered = data.date_administered
    vax.expiry_date = data.expiry_date

    if data.batch_number:
        vax.batch_number_encrypted = encrypt(data.batch_number)
        vax.batch_number_masked = mask_value(data.batch_number)
    else:
        vax.batch_number_encrypted = None
        vax.batch_number_masked = None

    if data.notes:
        vax.notes_encrypted = encrypt(data.notes)
        vax.notes_masked = mask_value(data.notes)
    else:
        vax.notes_encrypted = None
        vax.notes_masked = None

    db.commit()
    db.refresh(vax)
    log.info(f"Updated vaccination: {vax.vaccine_name}")
    return _vaccination_to_response(vax)


@router.delete("/vaccinations/{vax_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vaccination(
    vax_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a vaccination record."""
    vax = db.query(VaultVaccination).filter(VaultVaccination.id == vax_id).first()
    if not vax:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")
    log.info(f"Deleting vaccination: {vax.vaccine_name}")
    db.delete(vax)
    db.commit()
