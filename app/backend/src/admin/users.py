from datetime import date
from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth.session import get_admin_user
from ..database import get_db
from ..log_config import get_logger
from ..models import TripParticipant, User

log = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["admin-users"])


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    nickname: str | None
    picture: str | None
    birthday: date | None
    is_admin: bool
    is_active: bool
    trips_count: int = 0

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserResponse]


PLACEHOLDER_DOMAIN = "@placeholder.local"


def validate_email_or_placeholder(email: str) -> str:
    """Allow @placeholder.local or validate as proper email."""
    email = email.strip().lower()
    if email.endswith(PLACEHOLDER_DOMAIN):
        # Basic check: something before @
        if len(email) > len(PLACEHOLDER_DOMAIN):
            return email
        raise ValueError("Invalid placeholder email")
    # Validate as proper email
    try:
        result = validate_email(email, check_deliverability=False)
        return result.normalized
    except EmailNotValidError:
        raise ValueError("Invalid email address")


class UserCreateRequest(BaseModel):
    email: str
    name: str | None = None
    nickname: str | None = None
    birthday: date | None = None

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_or_placeholder(v)


class UserUpdateRequest(BaseModel):
    email: str | None = None
    name: str | None = None
    nickname: str | None = None
    birthday: date | None = None
    is_admin: bool | None = None

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validate_email_or_placeholder(v)


@router.get("/", response_model=UserListResponse)
def list_users(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> UserListResponse:
    """List all users except the current admin."""
    rows = (
        db.query(User, func.count(TripParticipant.id).label("trips_count"))
        .outerjoin(TripParticipant, TripParticipant.user_id == User.id)
        .filter(User.id != admin.id)
        .group_by(User.id)
        .order_by(User.email)
        .all()
    )
    result = []
    for user, trips_count in rows:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "nickname": user.nickname,
            "picture": user.picture,
            "birthday": user.birthday,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "trips_count": trips_count,
        }
        result.append(UserResponse.model_validate(user_dict))
    return UserListResponse(users=result)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> UserResponse:
    """Create a new user (is_active=false until first login)."""
    # Check for existing email (case-insensitive)
    existing = db.query(User).filter(User.email.ilike(data.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        email=data.email.lower(),
        name=data.name,
        nickname=data.nickname,
        birthday=data.birthday,
        is_admin=False,
        is_active=False,  # Pending until first login
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log.info(f"Created user: {user.email} by admin {admin.email}")
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update user email, name, nickname, or is_admin status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from modifying their own record
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify your own user record",
        )

    if data.email is not None:
        # Check for duplicate email (case-insensitive)
        existing = db.query(User).filter(User.email.ilike(data.email), User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        user.email = data.email.lower()

    if data.name is not None:
        user.name = data.name
    if data.nickname is not None:
        user.nickname = data.nickname
    if data.birthday is not None:
        user.birthday = data.birthday
    if data.is_admin is not None:
        user.is_admin = data.is_admin

    db.commit()
    db.refresh(user)
    log.info(f"Updated user: {user.email} by admin {admin.email}")
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from deleting themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own user record",
        )

    log.info(f"Deleting user: {user.email} by admin {admin.email}")
    db.delete(user)
    db.commit()
