from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from ..crypto import decrypt
from ..models import (
    VaultAddress,
    VaultDocument,
    VaultFile,
    VaultLoyaltyProgram,
    VaultTravelDoc,
    VaultVaccination,
)

# --- Document models ---


class DocumentRequest(BaseModel):
    user_id: int
    doc_type: Literal["passport", "id_card", "drivers_license"]
    label: str
    proper_name: str | None = None
    issuing_country: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    number: str | None = None
    notes: str | None = None


class VaultFileResponse(BaseModel):
    id: int
    label: str | None
    mime_type: str
    file_size: int
    sort_order: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    doc_type: str
    label: str
    proper_name: str | None
    issuing_country: str | None
    issue_date: date | None
    expiry_date: date | None
    number_masked: str | None
    number_decrypted: str | None = None
    notes_masked: str | None
    notes_decrypted: str | None = None
    is_archived: bool = False
    files: list[VaultFileResponse] = []


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


# --- Loyalty Program models ---


class LoyaltyProgramRequest(BaseModel):
    user_id: int
    program_name: str
    alliance: Literal["star_alliance", "oneworld", "skyteam", "none"] = "none"
    tier: str | None = None
    membership_number: str | None = None
    notes: str | None = None


class LoyaltyProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    program_name: str
    alliance: str
    tier: str | None
    membership_number_masked: str | None
    membership_number_decrypted: str | None = None
    notes_masked: str | None
    notes_decrypted: str | None = None
    is_favorite: bool = False


class LoyaltyProgramListResponse(BaseModel):
    programs: list[LoyaltyProgramResponse]


# --- Program options models ---


class ProgramOptionAirline(BaseModel):
    name: str
    flights_count: int


class ProgramOption(BaseModel):
    program_name: str
    alliance: str
    airlines: list[ProgramOptionAirline]
    total_flights: int


class ProgramOptionsResponse(BaseModel):
    programs: list[ProgramOption]


# --- Vaccination models ---


class VaccinationRequest(BaseModel):
    user_id: int
    vaccine_name: str
    brand_name: str | None = None
    dose_type: str | None = None
    date_administered: date | None = None
    expiry_date: date | None = None
    batch_number: str | None = None
    notes: str | None = None


class VaccinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    vaccine_name: str
    brand_name: str | None
    dose_type: str | None
    date_administered: date | None
    expiry_date: date | None
    batch_number_masked: str | None
    batch_number_decrypted: str | None = None
    notes_masked: str | None
    notes_decrypted: str | None = None
    files: list[VaultFileResponse] = []


class VaccinationListResponse(BaseModel):
    vaccinations: list[VaccinationResponse]


# --- Address models ---


class AddressRequest(BaseModel):
    name: str
    address: str
    country_code: str | None = None
    user_id: int | None = None
    notes: str | None = None


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    country_code: str | None
    user_id: int | None = None
    user_name: str | None = None
    user_picture: str | None = None
    notes_masked: str | None
    notes_decrypted: str | None = None


class AddressListResponse(BaseModel):
    addresses: list[AddressResponse]


class AddressSearchResult(BaseModel):
    display_name: str
    country_code: str | None = None


class AddressSearchResponse(BaseModel):
    results: list[AddressSearchResult]


# --- Travel Document models ---


class TravelDocRequest(BaseModel):
    user_id: int
    doc_type: str
    label: str
    document_id: int | None = None
    country_code: str | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    entry_type: str | None = None
    notes: str | None = None


class TravelDocResponse(BaseModel):
    id: int
    user_id: int
    doc_type: str
    label: str
    document_id: int | None = None
    passport_label: str | None = None
    country_code: str | None
    valid_from: date | None
    valid_until: date | None
    entry_type: str | None
    notes_masked: str | None
    notes_decrypted: str | None = None
    files: list[VaultFileResponse] = []
    trip_ids: list[int] = []


class TravelDocListResponse(BaseModel):
    travel_docs: list[TravelDocResponse]


# --- AI Extraction model ---


class ExtractedMetadataResponse(BaseModel):
    doc_type: str | None = None
    label: str | None = None
    country_code: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    entry_type: str | None = None
    notes: str | None = None
    document_id: int | None = None
    error: str | None = None


# --- Helper functions ---


def _clean_number(value: str | None) -> str | None:
    """Strip whitespace and dashes from membership/document numbers."""
    if not value:
        return value
    return value.replace(" ", "").replace("-", "").replace("\t", "").strip()


def _files_to_response(files: list[VaultFile]) -> list[VaultFileResponse]:
    return [
        VaultFileResponse(
            id=f.id,
            label=f.label,
            mime_type=f.mime_type,
            file_size=f.file_size,
            sort_order=f.sort_order,
        )
        for f in sorted(files, key=lambda x: x.sort_order)
    ]


def _doc_to_response(doc: VaultDocument) -> DocumentResponse:
    number_decrypted = None
    if doc.number_encrypted:
        number_decrypted = decrypt(doc.number_encrypted)
    notes_decrypted = None
    if doc.notes_encrypted:
        notes_decrypted = decrypt(doc.notes_encrypted)
    return DocumentResponse(
        id=doc.id,
        user_id=doc.user_id,
        doc_type=doc.doc_type,
        label=doc.label,
        proper_name=doc.proper_name,
        issuing_country=doc.issuing_country,
        issue_date=doc.issue_date,
        expiry_date=doc.expiry_date,
        number_masked=doc.number_masked,
        number_decrypted=number_decrypted,
        notes_masked=doc.notes_masked,
        notes_decrypted=notes_decrypted,
        is_archived=doc.is_archived,
        files=_files_to_response(doc.files),
    )


def _program_to_response(prog: VaultLoyaltyProgram) -> LoyaltyProgramResponse:
    membership_decrypted = None
    if prog.membership_number_encrypted:
        membership_decrypted = decrypt(prog.membership_number_encrypted)
    notes_decrypted = None
    if prog.notes_encrypted:
        notes_decrypted = decrypt(prog.notes_encrypted)
    return LoyaltyProgramResponse(
        id=prog.id,
        user_id=prog.user_id,
        program_name=prog.program_name,
        alliance=prog.alliance,
        tier=prog.tier,
        membership_number_masked=prog.membership_number_masked,
        membership_number_decrypted=membership_decrypted,
        notes_masked=prog.notes_masked,
        notes_decrypted=notes_decrypted,
        is_favorite=prog.is_favorite,
    )


def _vaccination_to_response(vax: VaultVaccination) -> VaccinationResponse:
    batch_decrypted = None
    if vax.batch_number_encrypted:
        batch_decrypted = decrypt(vax.batch_number_encrypted)
    notes_decrypted = None
    if vax.notes_encrypted:
        notes_decrypted = decrypt(vax.notes_encrypted)
    return VaccinationResponse(
        id=vax.id,
        user_id=vax.user_id,
        vaccine_name=vax.vaccine_name,
        brand_name=vax.brand_name,
        dose_type=vax.dose_type,
        date_administered=vax.date_administered,
        expiry_date=vax.expiry_date,
        batch_number_masked=vax.batch_number_masked,
        batch_number_decrypted=batch_decrypted,
        notes_masked=vax.notes_masked,
        notes_decrypted=notes_decrypted,
        files=_files_to_response(vax.files),
    )


def _address_to_response(addr: VaultAddress) -> AddressResponse:
    notes_decrypted = None
    if addr.notes_encrypted:
        notes_decrypted = decrypt(addr.notes_encrypted)
    return AddressResponse(
        id=addr.id,
        name=addr.name,
        address=addr.address,
        country_code=addr.country_code,
        user_id=addr.user_id,
        user_name=addr.user.nickname or addr.user.name if addr.user else None,
        user_picture=addr.user.picture if addr.user else None,
        notes_masked=addr.notes_masked,
        notes_decrypted=notes_decrypted,
    )


def _travel_doc_to_response(td: VaultTravelDoc) -> TravelDocResponse:
    notes_decrypted = None
    if td.notes_encrypted:
        notes_decrypted = decrypt(td.notes_encrypted)
    return TravelDocResponse(
        id=td.id,
        user_id=td.user_id,
        doc_type=td.doc_type,
        label=td.label,
        document_id=td.document_id,
        passport_label=td.passport.label if td.passport else None,
        country_code=td.country_code,
        valid_from=td.valid_from,
        valid_until=td.valid_until,
        entry_type=td.entry_type,
        notes_masked=td.notes_masked,
        notes_decrypted=notes_decrypted,
        files=_files_to_response(td.files),
        trip_ids=[t.trip_id for t in td.trips],
    )


def _match_passport(passport_number: str, db: Session) -> int | None:
    """Try to match an extracted passport number against vault documents."""
    normalized = passport_number.replace(" ", "").replace("-", "").upper()
    if not normalized:
        return None
    passports = (
        db.query(VaultDocument)
        .filter(VaultDocument.doc_type == "passport", VaultDocument.is_archived.is_(False))
        .all()
    )
    for doc in passports:
        if doc.number_encrypted:
            stored = decrypt(doc.number_encrypted).replace(" ", "").replace("-", "").upper()
            if stored == normalized:
                return doc.id
    return None
