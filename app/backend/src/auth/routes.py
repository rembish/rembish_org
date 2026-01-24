from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.config import Config

from ..config import settings
from ..database import get_db
from ..logging import get_logger
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
config = Config(environ={
    "GOOGLE_CLIENT_ID": settings.google_client_id,
    "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
})
oauth = OAuth(config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Allowed email for login
ALLOWED_EMAIL = "alex@rembish.org"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    picture: str | None
    is_admin: bool

    class Config:
        from_attributes = True


@router.get("/me")
def get_me(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> UserResponse | None:
    """Get current logged-in user info, or null if not logged in."""
    if not user:
        return None
    return UserResponse.model_validate(user)


@router.get("/login")
async def login(request: Request):
    """Redirect to Google OAuth login."""
    if not settings.google_client_id:
        log.warning("OAuth login attempted but not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured",
        )
    log.debug("Initiating Google OAuth login")
    redirect_uri = f"{settings.frontend_url}/api/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    """Handle OAuth callback from Google."""
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

    # Only allow specific email
    if email.lower() != ALLOWED_EMAIL.lower():
        log.warning(f"Login rejected for unauthorized email: {email}")
        response = RedirectResponse(url=settings.frontend_url, status_code=302)
        return response

    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name=userinfo.get("name"),
            picture=userinfo.get("picture"),
            is_admin=True,  # First user (you) is admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        log.info(f"Created new user: {email}")
    else:
        # Update name/picture if changed
        user.name = userinfo.get("name")
        user.picture = userinfo.get("picture")
        db.commit()
        log.info(f"User logged in: {email}")

    # Create session and redirect
    session_token = create_session_token(user.id)
    response = RedirectResponse(url=settings.frontend_url, status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_MAX_AGE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
    )
    return response


@router.post("/logout")
def logout():
    """Log out by clearing the session cookie."""
    log.debug("User logged out")
    response = RedirectResponse(url=settings.frontend_url, status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@router.get("/logout")
def logout_get():
    """Log out (GET version for simple links)."""
    return logout()
