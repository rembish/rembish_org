from datetime import date
from typing import Annotated, cast

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
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
    VAULT_COOKIE_NAME,
    VAULT_MAX_AGE,
    create_session_token,
    create_vault_token,
    get_current_user_optional,
    verify_vault_token,
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
VAULT_FLOW_COOKIE_NAME = "auth_vault_flow"


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
    is_vault_flow = request.cookies.get(VAULT_FLOW_COOKIE_NAME) == "1"

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
        response.delete_cookie(VAULT_FLOW_COOKIE_NAME, path="/")
        return response

    # --- Vault re-auth flow ---
    if is_vault_flow:
        if not user.is_admin:
            log.warning(f"Vault auth rejected for non-admin: {email}")
            response = RedirectResponse(url=f"{settings.frontend_url}/admin", status_code=302)
            response.delete_cookie(VAULT_FLOW_COOKIE_NAME, path="/")
            return response

        vault_tok = create_vault_token(user.id)
        response = RedirectResponse(url=f"{settings.frontend_url}/admin/vault", status_code=302)
        response.set_cookie(
            key=VAULT_COOKIE_NAME,
            value=vault_tok,
            max_age=VAULT_MAX_AGE,
            path="/",
            httponly=True,
            samesite="lax",
            secure=settings.env == "production",
        )
        response.delete_cookie(VAULT_FLOW_COOKIE_NAME, path="/")
        log.info(f"Vault unlocked for: {email}")
        return response

    # --- Regular login flow ---

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


# --- Vault re-authentication ---


@router.get("/vault/login")
async def vault_login(request: Request) -> RedirectResponse:
    """Redirect to Google OAuth for vault re-authentication.

    Reuses the same /api/auth/callback redirect URI (already registered in Google
    Cloud Console). A marker cookie distinguishes vault flow from regular login.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured",
        )
    # Reuse existing callback URI — no separate registration needed
    redirect_uri = f"{settings.frontend_url}/api/auth/callback"
    response = cast(
        RedirectResponse,
        await oauth.google.authorize_redirect(request, redirect_uri),
    )
    # Mark this as a vault flow so callback knows to issue vault token
    response.set_cookie(
        key=VAULT_FLOW_COOKIE_NAME,
        value="1",
        max_age=300,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.env == "production",
    )
    return response


class VaultStatusResponse(BaseModel):
    unlocked: bool


@router.post("/vault/lock")
def vault_lock() -> JSONResponse:
    """Lock the vault by clearing the vault cookie."""
    log.debug("Vault locked manually")
    response = JSONResponse(content={"locked": True})
    response.delete_cookie(VAULT_COOKIE_NAME, path="/")
    return response


@router.get("/vault/status")
def vault_status(
    user: Annotated[User | None, Depends(get_current_user_optional)],
    vault_auth: Annotated[str | None, Cookie(alias=VAULT_COOKIE_NAME)] = None,
) -> VaultStatusResponse:
    """Check if vault is currently unlocked."""
    if not user or not user.is_admin or not vault_auth:
        return VaultStatusResponse(unlocked=False)
    data = verify_vault_token(vault_auth)
    if not data or data.get("user_id") != user.id:
        return VaultStatusResponse(unlocked=False)
    return VaultStatusResponse(unlocked=True)
