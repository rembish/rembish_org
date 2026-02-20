import time
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_vault_user
from ..crypto import encrypt, mask_value
from ..database import get_db
from ..log_config import get_logger
from ..models import User, VaultAddress
from .vault_models import (
    AddressListResponse,
    AddressRequest,
    AddressResponse,
    AddressSearchResponse,
    AddressSearchResult,
    _address_to_response,
)

log = get_logger(__name__)
router = APIRouter()

# Nominatim rate limiting — reuse same pattern as trips_nominatim.py
_nominatim_last_request: float = 0.0
_NOMINATIM_COOLDOWN = 1.0  # seconds between requests


def _format_postal_address(addr: dict[str, str]) -> str | None:
    """Build a postal-friendly address from Nominatim address details."""
    # Street line: road + house_number
    road = addr.get("road", "")
    house = addr.get("house_number", "")
    street = f"{road} {house}".strip() if road else house

    # City: prefer city > town > village > county
    city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or ""

    postcode = addr.get("postcode", "")
    state = addr.get("state", "")
    country = addr.get("country", "")

    # Build lines
    lines: list[str] = []
    if street:
        lines.append(street)
    # City line with postcode
    if postcode and city:
        lines.append(f"{postcode} {city}")
    elif city:
        lines.append(city)
    elif postcode:
        lines.append(postcode)
    # State only if different from city
    if state and state != city:
        lines.append(state)
    if country:
        lines.append(country)

    return "\n".join(lines) if lines else None


@router.get("/address-search", response_model=AddressSearchResponse)
def address_search(
    q: str,
    admin: Annotated[User, Depends(get_vault_user)],
) -> AddressSearchResponse:
    """Search Nominatim for address autocomplete."""
    global _nominatim_last_request

    if not q.strip():
        return AddressSearchResponse(results=[])

    # Enforce cooldown
    elapsed = time.time() - _nominatim_last_request
    if elapsed < _NOMINATIM_COOLDOWN:
        time.sleep(_NOMINATIM_COOLDOWN - elapsed)

    try:
        _nominatim_last_request = time.time()
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": q,
                "format": "json",
                "addressdetails": "1",
                "accept-language": "en",
                "limit": "5",
            },
            headers={
                "User-Agent": "rembish.org travel tracker (hobby project)",
                "Accept-Language": "en",
            },
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        log.exception("Nominatim address search failed")
        return AddressSearchResponse(results=[])

    results: list[AddressSearchResult] = []
    for item in data:
        addr_details = item.get("address", {})
        cc = addr_details.get("country_code", "").upper() or None
        formatted = _format_postal_address(addr_details)
        results.append(
            AddressSearchResult(
                display_name=formatted or item.get("display_name", ""),
                country_code=cc,
            )
        )
    return AddressSearchResponse(results=results)


@router.get("/addresses", response_model=AddressListResponse)
def list_addresses(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
    search: str | None = None,
) -> AddressListResponse:
    """List addresses, optionally filtered by name/address search."""
    query = db.query(VaultAddress).options(joinedload(VaultAddress.user))
    if search:
        pattern = f"%{search}%"
        query = query.filter(VaultAddress.name.ilike(pattern) | VaultAddress.address.ilike(pattern))
    query = query.order_by(VaultAddress.name)
    addrs = query.all()
    return AddressListResponse(addresses=[_address_to_response(a) for a in addrs])


@router.post(
    "/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    data: AddressRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> AddressResponse:
    """Create an address with encrypted notes."""
    addr = VaultAddress(
        name=data.name,
        address=data.address,
        country_code=data.country_code.upper() if data.country_code else None,
        user_id=data.user_id,
    )
    if data.notes:
        addr.notes_encrypted = encrypt(data.notes)
        addr.notes_masked = mask_value(data.notes)

    db.add(addr)
    db.commit()
    db.refresh(addr)
    log.info(f"Created address: {addr.name}")
    return _address_to_response(addr)


@router.put("/addresses/{addr_id}", response_model=AddressResponse)
def update_address(
    addr_id: int,
    data: AddressRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> AddressResponse:
    """Update an address (re-encrypts notes)."""
    addr = (
        db.query(VaultAddress)
        .options(joinedload(VaultAddress.user))
        .filter(VaultAddress.id == addr_id)
        .first()
    )
    if not addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

    addr.name = data.name
    addr.address = data.address
    addr.country_code = data.country_code.upper() if data.country_code else None
    addr.user_id = data.user_id

    if data.notes:
        addr.notes_encrypted = encrypt(data.notes)
        addr.notes_masked = mask_value(data.notes)
    else:
        addr.notes_encrypted = None
        addr.notes_masked = None

    db.commit()
    db.refresh(addr)
    log.info(f"Updated address: {addr.name}")
    return _address_to_response(addr)


@router.delete("/addresses/{addr_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    addr_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete an address."""
    addr = db.query(VaultAddress).filter(VaultAddress.id == addr_id).first()
    if not addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    log.info(f"Deleting address: {addr.name}")
    db.delete(addr)
    db.commit()
