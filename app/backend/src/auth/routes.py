from datetime import date
from typing import Annotated, cast

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from starlette.config import Config

from ..config import settings
from ..database import get_db
from ..log_config import get_logger
from ..models import User
from .session import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE,
    create_session_token,
    get_current_user_optional,
)

log = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth setup
config = Config(
    environ={
        "GOOGLE_CLIENT_ID": settings.google_client_id,
        "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
    }
)
oauth = OAuth(config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None
    nickname: str | None
    picture: str | None
    birthday: date | None
    is_admin: bool


@router.get("/me")
def get_me(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> UserResponse | None:
    """Get current logged-in user info, or null if not logged in."""
    if not user:
        return None
    return UserResponse.model_validate(user)


REDIRECT_COOKIE_NAME = "auth_redirect"


def _validate_redirect(redirect: str | None) -> str:
    """Validate redirect path to prevent open redirect attacks."""
    if not redirect or not redirect.startswith("/") or redirect.startswith("//"):
        return "/"
    return redirect


@router.get("/login")
async def login(request: Request, redirect: str | None = None) -> RedirectResponse:
    """Redirect to Google OAuth login."""
    if not settings.google_client_id:
        log.warning("OAuth login attempted but not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured",
        )
    log.debug("Initiating Google OAuth login")
    redirect_uri = f"{settings.frontend_url}/api/auth/callback"
    response = cast(RedirectResponse, await oauth.google.authorize_redirect(request, redirect_uri))
    # Store intended redirect in cookie for callback to read
    validated_redirect = _validate_redirect(redirect)
    if validated_redirect != "/":
        response.set_cookie(
            key=REDIRECT_COOKIE_NAME,
            value=validated_redirect,
            max_age=300,  # 5 minutes, enough for OAuth flow
            path="/",
            httponly=True,
            samesite="lax",
            secure=settings.env == "production",
        )
    return response


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """Handle OAuth callback from Google."""
    # Get redirect target from cookie (set during login)
    redirect_path = request.cookies.get(REDIRECT_COOKIE_NAME, "/")
    redirect_path = _validate_redirect(redirect_path)
    redirect_url = f"{settings.frontend_url}{redirect_path}"

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        log.exception("OAuth authorization failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth authorization failed",
        )

    userinfo = token.get("userinfo")
    if not userinfo:
        log.error("OAuth callback missing userinfo in token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info",
        )

    email = userinfo.get("email")
    if not email:
        log.error("OAuth callback missing email in userinfo")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided",
        )

    # Check if user exists in database (case-insensitive)
    user = db.query(User).filter(User.email.ilike(email)).first()
    if not user:
        log.warning(f"Login rejected - email not in users table: {email}")
        response = RedirectResponse(url=settings.frontend_url, status_code=302)
        response.delete_cookie(REDIRECT_COOKIE_NAME, path="/")
        return response

    # Update name/picture from Google profile
    user.name = userinfo.get("name")
    user.picture = userinfo.get("picture")

    # Activate user on first login
    if not user.is_active:
        user.is_active = True
        log.info(f"User activated on first login: {email}")

    db.commit()
    log.info(f"User logged in: {email}")

    # Create session and redirect
    session_token = create_session_token(user.id)
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_MAX_AGE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.env == "production",
    )
    # Clean up redirect cookie
    response.delete_cookie(REDIRECT_COOKIE_NAME, path="/")
    return response


@router.post("/logout")
def logout(redirect: str | None = None) -> RedirectResponse:
    """Log out by clearing the session cookie."""
    log.debug("User logged out")
    redirect_path = _validate_redirect(redirect)
    redirect_url = f"{settings.frontend_url}{redirect_path}"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@router.get("/logout")
def logout_get(redirect: str | None = None) -> RedirectResponse:
    """Log out (GET version for simple links)."""
    return logout(redirect)
