from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth.session import get_vault_user
from ..crypto import encrypt, mask_value
from ..database import get_db
from ..log_config import get_logger
from ..models import Flight, User, VaultLoyaltyProgram
from .vault_data import AIRLINE_TO_PROGRAM, LOYALTY_PROGRAMS
from .vault_models import (
    LoyaltyProgramListResponse,
    LoyaltyProgramRequest,
    LoyaltyProgramResponse,
    ProgramOption,
    ProgramOptionAirline,
    ProgramOptionsResponse,
    _clean_number,
    _program_to_response,
)

log = get_logger(__name__)
router = APIRouter()


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
