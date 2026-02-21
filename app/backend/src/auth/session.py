from typing import Annotated, Any, cast

from fastapi import Cookie, Depends, HTTPException, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User

SESSION_COOKIE_NAME = "auth"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

VAULT_COOKIE_NAME = "vault_auth"
VAULT_MAX_AGE = 600  # 10 minutes

serializer = URLSafeTimedSerializer(settings.secret_key)


def create_session_token(user_id: int) -> str:
    """Create a signed session token containing the user ID."""
    return serializer.dumps({"user_id": user_id})


def verify_session_token(token: str) -> dict[str, Any] | None:
    """Verify and decode a session token. Returns None if invalid."""
    try:
        return cast(dict[str, Any], serializer.loads(token, max_age=SESSION_MAX_AGE))
    except BadSignature:
        return None


def get_current_user_optional(
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
    db: Session = Depends(get_db),
) -> User | None:
    """Get current user from session cookie, or None if not logged in."""
    if not session:
        return None

    data = verify_session_token(session)
    if not data or "user_id" not in data:
        return None

    user = db.query(User).filter(User.id == data["user_id"]).first()
    return user


def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    """Get current user, raising 401 if not logged in."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def get_admin_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user, raising 403 if not admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def get_trips_viewer(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Allow admin or viewer. 403 otherwise."""
    if user.role not in ("admin", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return user


def create_vault_token(user_id: int) -> str:
    """Create a signed vault session token."""
    return serializer.dumps({"user_id": user_id, "vault": True})


def verify_vault_token(token: str) -> dict[str, Any] | None:
    """Verify a vault token. Returns None if invalid or expired."""
    try:
        data = cast(dict[str, Any], serializer.loads(token, max_age=VAULT_MAX_AGE))
        if not data.get("vault"):
            return None
        return data
    except BadSignature:
        return None


def is_vault_unlocked(
    user: Annotated[User, Depends(get_admin_user)],
    vault_auth: Annotated[str | None, Cookie(alias=VAULT_COOKIE_NAME)] = None,
) -> bool:
    """Check if vault is currently unlocked (non-throwing)."""
    if not vault_auth:
        return False
    data = verify_vault_token(vault_auth)
    return bool(data and data.get("user_id") == user.id)


def is_vault_unlocked_for_viewer(
    user: Annotated[User, Depends(get_trips_viewer)],
    vault_auth: Annotated[str | None, Cookie(alias=VAULT_COOKIE_NAME)] = None,
) -> bool:
    """Vault check for viewer-accessible endpoints. Viewers always get False."""
    if not user.is_admin or not vault_auth:
        return False
    data = verify_vault_token(vault_auth)
    return bool(data and data.get("user_id") == user.id)


def get_vault_user(
    user: Annotated[User, Depends(get_admin_user)],
    vault_auth: Annotated[str | None, Cookie(alias=VAULT_COOKIE_NAME)] = None,
) -> User:
    """Get admin user with valid vault session. Raises 401 if vault is locked."""
    if not vault_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="vault_locked",
        )
    data = verify_vault_token(vault_auth)
    if not data or data.get("user_id") != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="vault_locked",
        )
    return user
