from typing import Annotated, Any, cast

from fastapi import Cookie, Depends, HTTPException, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User

SESSION_COOKIE_NAME = "auth"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

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
