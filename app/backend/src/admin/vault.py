from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_vault_user
from ..crypto import decrypt, encrypt, mask_value
from ..database import get_db
from ..log_config import get_logger
from ..models import (
    Flight,
    Trip,
    TripTravelDoc,
    User,
    VaultDocument,
    VaultFile,
    VaultLoyaltyProgram,
    VaultTravelDoc,
    VaultVaccination,
)
from ..models.vault import TripPassport

# Loyalty program → alliance + member airlines (all current alliance members)
LOYALTY_PROGRAMS: dict[str, dict[str, str | list[str]]] = {
    # ── Star Alliance ──
    "Miles & More": {
        "alliance": "star_alliance",
        "airlines": [
            "Austrian Airlines",
            "Brussels Airlines",
            "Croatia Airlines",
            "LOT Polish Airlines",
            "Lufthansa",
            "SWISS",
        ],
    },
    "Miles&Smiles": {
        "alliance": "star_alliance",
        "airlines": ["Turkish Airlines"],
    },
    "Miles+Bonus": {
        "alliance": "star_alliance",
        "airlines": ["Aegean Airlines"],
    },
    "Aeroplan": {
        "alliance": "star_alliance",
        "airlines": ["Air Canada"],
    },
    "MileagePlus": {
        "alliance": "star_alliance",
        "airlines": ["United Airlines"],
    },
    "KrisFlyer": {
        "alliance": "star_alliance",
        "airlines": ["Singapore Airlines"],
    },
    "Miles&Go": {
        "alliance": "star_alliance",
        "airlines": ["TAP Air Portugal"],
    },
    "ANA Mileage Club": {
        "alliance": "star_alliance",
        "airlines": ["ANA"],
    },
    "Royal Orchid Plus": {
        "alliance": "star_alliance",
        "airlines": ["Thai Airways"],
    },
    "Infinity MileageLands": {
        "alliance": "star_alliance",
        "airlines": ["EVA Air"],
    },
    "LifeMiles": {
        "alliance": "star_alliance",
        "airlines": ["Avianca"],
    },
    "ConnectMiles": {
        "alliance": "star_alliance",
        "airlines": ["Copa Airlines"],
    },
    "EgyptAir Plus": {
        "alliance": "star_alliance",
        "airlines": ["EgyptAir"],
    },
    "ShebaMiles": {
        "alliance": "star_alliance",
        "airlines": ["Ethiopian Airlines"],
    },
    "Voyager": {
        "alliance": "star_alliance",
        "airlines": ["South African Airways"],
    },
    "PhoenixMiles": {
        "alliance": "star_alliance",
        "airlines": ["Air China"],
    },
    "Flying Returns": {
        "alliance": "star_alliance",
        "airlines": ["Air India"],
    },
    "Asiana Club": {
        "alliance": "star_alliance",
        "airlines": ["Asiana Airlines"],
    },
    # ── Oneworld ──
    "Executive Club": {
        "alliance": "oneworld",
        "airlines": ["British Airways"],
    },
    "Iberia Plus": {
        "alliance": "oneworld",
        "airlines": ["Iberia"],
    },
    "Vueling Club": {
        "alliance": "oneworld",
        "airlines": ["Vueling"],
    },
    "AerClub": {
        "alliance": "oneworld",
        "airlines": ["Aer Lingus"],
    },
    "AAdvantage": {
        "alliance": "oneworld",
        "airlines": ["American Airlines"],
    },
    "Qantas Frequent Flyer": {
        "alliance": "oneworld",
        "airlines": ["Qantas"],
    },
    "Asia Miles": {
        "alliance": "oneworld",
        "airlines": ["Cathay Pacific"],
    },
    "Finnair Plus": {
        "alliance": "oneworld",
        "airlines": ["Finnair"],
    },
    "JAL Mileage Bank": {
        "alliance": "oneworld",
        "airlines": ["Japan Airlines"],
    },
    "Enrich": {
        "alliance": "oneworld",
        "airlines": ["Malaysia Airlines"],
    },
    "Privilege Club": {
        "alliance": "oneworld",
        "airlines": ["Qatar Airways"],
    },
    "Mileage Plan": {
        "alliance": "oneworld",
        "airlines": ["Alaska Airlines"],
    },
    "Royal Club": {
        "alliance": "oneworld",
        "airlines": ["Royal Jordanian"],
    },
    "Safar Flyer": {
        "alliance": "oneworld",
        "airlines": ["Royal Air Maroc"],
    },
    "FlySmiLes": {
        "alliance": "oneworld",
        "airlines": ["SriLankan Airlines"],
    },
    "Sindbad": {
        "alliance": "oneworld",
        "airlines": ["Oman Air"],
    },
    "Fiji Airways Tabua Club": {
        "alliance": "oneworld",
        "airlines": ["Fiji Airways"],
    },
    "LATAM Pass": {
        "alliance": "oneworld",
        "airlines": ["LATAM Airlines"],
    },
    # ── SkyTeam ──
    "Flying Blue": {
        "alliance": "skyteam",
        "airlines": ["Air France", "KLM"],
    },
    "SkyMiles": {
        "alliance": "skyteam",
        "airlines": ["Delta Air Lines"],
    },
    "SKYPASS": {
        "alliance": "skyteam",
        "airlines": ["Korean Air"],
    },
    "EuroBonus": {
        "alliance": "skyteam",
        "airlines": ["Scandinavian Airlines"],
    },
    "Club Premier": {
        "alliance": "skyteam",
        "airlines": ["AeroMexico"],
    },
    "Volare": {
        "alliance": "skyteam",
        "airlines": ["ITA Airways"],
    },
    "Alfursan": {
        "alliance": "skyteam",
        "airlines": ["Saudia"],
    },
    "Lotusmiles": {
        "alliance": "skyteam",
        "airlines": ["Vietnam Airlines"],
    },
    "Flying Club": {
        "alliance": "skyteam",
        "airlines": ["Virgin Atlantic"],
    },
    "Dynasty Flyer": {
        "alliance": "skyteam",
        "airlines": ["China Airlines"],
    },
    "Eastern Miles": {
        "alliance": "skyteam",
        "airlines": ["China Eastern"],
    },
    "Cedar Miles": {
        "alliance": "skyteam",
        "airlines": ["Middle East Airlines"],
    },
    "SUMA": {
        "alliance": "skyteam",
        "airlines": ["Air Europa"],
    },
    "Egret Club": {
        "alliance": "skyteam",
        "airlines": ["XiamenAir"],
    },
    "Aerolíneas Plus": {
        "alliance": "skyteam",
        "airlines": ["Aerolíneas Argentinas"],
    },
    "Asante": {
        "alliance": "skyteam",
        "airlines": ["Kenya Airways"],
    },
    "TAROM FrequentFlyer": {
        "alliance": "skyteam",
        "airlines": ["TAROM"],
    },
}

# Reverse: airline name → program name (built from LOYALTY_PROGRAMS)
AIRLINE_TO_PROGRAM: dict[str, str] = {}
for _prog_name, _prog_info in LOYALTY_PROGRAMS.items():
    for _airline in _prog_info["airlines"]:
        AIRLINE_TO_PROGRAM[str(_airline)] = _prog_name

log = get_logger(__name__)
router = APIRouter(prefix="/vault", tags=["admin-vault"])

# --- Pydantic models ---


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


# --- Helpers ---


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


# --- Document endpoints ---


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


# --- Loyalty Program endpoints ---


@router.get("/programs", response_model=LoyaltyProgramListResponse)
def list_programs(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
    user_id: int | None = None,
) -> LoyaltyProgramListResponse:
    """List loyalty programs, optionally filtered by user_id."""
    query = db.query(VaultLoyaltyProgram)
    if user_id is not None:
        query = query.filter(VaultLoyaltyProgram.user_id == user_id)
    query = query.order_by(VaultLoyaltyProgram.program_name)
    progs = query.all()
    return LoyaltyProgramListResponse(programs=[_program_to_response(p) for p in progs])


@router.post(
    "/programs",
    response_model=LoyaltyProgramResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_program(
    data: LoyaltyProgramRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> LoyaltyProgramResponse:
    """Create a loyalty program entry with encrypted fields."""
    prog = VaultLoyaltyProgram(
        user_id=data.user_id,
        program_name=data.program_name,
        alliance=data.alliance,
        tier=data.tier,
    )
    clean_num = _clean_number(data.membership_number)
    if clean_num:
        prog.membership_number_encrypted = encrypt(clean_num)
        prog.membership_number_masked = mask_value(clean_num)
    if data.notes:
        prog.notes_encrypted = encrypt(data.notes)
        prog.notes_masked = mask_value(data.notes)

    db.add(prog)
    db.commit()
    db.refresh(prog)
    log.info(f"Created loyalty program: {prog.program_name} for user_id={prog.user_id}")
    return _program_to_response(prog)


@router.put("/programs/{prog_id}", response_model=LoyaltyProgramResponse)
def update_program(
    prog_id: int,
    data: LoyaltyProgramRequest,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> LoyaltyProgramResponse:
    """Update a loyalty program (re-encrypts sensitive fields)."""
    prog = db.query(VaultLoyaltyProgram).filter(VaultLoyaltyProgram.id == prog_id).first()
    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty program not found"
        )

    prog.user_id = data.user_id
    prog.program_name = data.program_name
    prog.alliance = data.alliance
    prog.tier = data.tier

    clean_num = _clean_number(data.membership_number)
    if clean_num:
        prog.membership_number_encrypted = encrypt(clean_num)
        prog.membership_number_masked = mask_value(clean_num)
    else:
        prog.membership_number_encrypted = None
        prog.membership_number_masked = None

    if data.notes:
        prog.notes_encrypted = encrypt(data.notes)
        prog.notes_masked = mask_value(data.notes)
    else:
        prog.notes_encrypted = None
        prog.notes_masked = None

    db.commit()
    db.refresh(prog)
    log.info(f"Updated loyalty program: {prog.program_name}")
    return _program_to_response(prog)


@router.delete("/programs/{prog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(
    prog_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a loyalty program."""
    prog = db.query(VaultLoyaltyProgram).filter(VaultLoyaltyProgram.id == prog_id).first()
    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty program not found"
        )
    log.info(f"Deleting loyalty program: {prog.program_name}")
    db.delete(prog)
    db.commit()


@router.post("/programs/{prog_id}/favorite", response_model=LoyaltyProgramResponse)
def toggle_favorite(
    prog_id: int,
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> LoyaltyProgramResponse:
    """Toggle favorite status. Only one favorite per alliance per user."""
    prog = db.query(VaultLoyaltyProgram).filter(VaultLoyaltyProgram.id == prog_id).first()
    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty program not found"
        )

    if prog.is_favorite:
        # Unset favorite
        prog.is_favorite = False
    else:
        # Unset any existing favorite in the same alliance for this user
        db.query(VaultLoyaltyProgram).filter(
            VaultLoyaltyProgram.user_id == prog.user_id,
            VaultLoyaltyProgram.alliance == prog.alliance,
            VaultLoyaltyProgram.is_favorite.is_(True),
        ).update({"is_favorite": False})
        prog.is_favorite = True

    db.commit()
    db.refresh(prog)
    log.info(f"Toggled favorite: {prog.program_name} → {prog.is_favorite}")
    return _program_to_response(prog)


# --- Loyalty program options (from flight history) ---


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


@router.get("/program-options", response_model=ProgramOptionsResponse)
def list_program_options(
    admin: Annotated[User, Depends(get_vault_user)],
    db: Session = Depends(get_db),
) -> ProgramOptionsResponse:
    """List all known loyalty programs with flight counts from history."""
    rows = (
        db.query(Flight.airline_name, func.count(Flight.id))
        .filter(Flight.airline_name.is_not(None))
        .group_by(Flight.airline_name)
        .all()
    )
    airline_counts: dict[str, int] = {name: count for name, count in rows}

    # Build options from ALL known programs, not just flown airlines
    options: list[ProgramOption] = []
    for prog_name, info in LOYALTY_PROGRAMS.items():
        airlines_list = [str(a) for a in info["airlines"]]
        prog_airlines = [
            ProgramOptionAirline(name=a, flights_count=airline_counts.get(a, 0))
            for a in airlines_list
        ]
        total = sum(a.flights_count for a in prog_airlines)
        prog_airlines.sort(key=lambda a: a.flights_count, reverse=True)
        options.append(
            ProgramOption(
                program_name=prog_name,
                alliance=str(info["alliance"]),
                airlines=prog_airlines,
                total_flights=total,
            )
        )

    # Also add airlines from flight history not in any known program
    known_airlines = set(AIRLINE_TO_PROGRAM.keys())
    for airline_name, count in airline_counts.items():
        if airline_name not in known_airlines:
            options.append(
                ProgramOption(
                    program_name=airline_name,
                    alliance="none",
                    airlines=[ProgramOptionAirline(name=airline_name, flights_count=count)],
                    total_flights=count,
                )
            )

    options.sort(key=lambda p: p.total_flights, reverse=True)
    return ProgramOptionsResponse(programs=options)


# --- Vaccination Pydantic models ---


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


# --- Vaccination endpoints ---


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


# --- Travel Document Pydantic models ---


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
