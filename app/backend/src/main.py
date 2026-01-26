import time
from collections.abc import Callable
from typing import Any

import httpx
from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .auth import router as auth_router
from .config import settings
from .log_config import get_logger, setup_logging
from .travels import router as travels_router

# Initialize logging
setup_logging()
log = get_logger(__name__)

app = FastAPI(
    title="rembish.org API",
    version="0.12.2",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Session middleware for OAuth state
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if settings.env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(travels_router, prefix="/api")

# Spam protection settings
MIN_SUBMISSION_TIME_MS = 3000  # Reject forms submitted faster than 3 seconds


def send_telegram_message(text: str) -> bool:
    """Send message to Telegram chat."""
    token = settings.telegram_token
    chat_id = settings.telegram_chat_id

    if not token or not chat_id:
        log.debug("Telegram not configured, skipping notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = httpx.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
        )
        if response.is_success:
            log.info("Telegram notification sent")
            return True
        else:
            log.error(f"Telegram API error: {response.status_code} - {response.text}")
            return False
    except Exception:
        log.exception("Failed to send Telegram notification")
        return False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/info")
def info() -> dict[str, str]:
    return {
        "name": "rembish.org",
        "version": "0.12.2",
    }


def verify_turnstile(token: str) -> bool:
    """Verify Cloudflare Turnstile token."""
    if not settings.turnstile_secret:
        return True  # Skip verification if not configured (dev)

    try:
        response = httpx.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": settings.turnstile_secret,
                "response": token,
            },
        )
        result = response.json()
        return bool(result.get("success", False))
    except Exception:
        log.exception("Turnstile verification failed")
        return False


@app.post("/api/v1/contact")
def contact(
    name: str = Form(..., min_length=2),
    email: EmailStr = Form(...),
    subject: str = Form(""),
    message: str = Form(..., min_length=10),
    website: str = Form(""),  # Honeypot
    ts: str = Form("0"),  # Timestamp when form was loaded
    cf_turnstile_response: str = Form(""),  # Turnstile token
) -> dict[str, str]:
    # Spam check 1: Honeypot field should be empty
    if website:
        log.info(f"Honeypot triggered from {email}")
        return {"status": "ok"}

    # Spam check 2: Form submitted too quickly
    try:
        loaded_ts = int(ts)
        elapsed_ms = int(time.time() * 1000) - loaded_ts
        if elapsed_ms < MIN_SUBMISSION_TIME_MS:
            log.info(f"Speed check triggered from {email} ({elapsed_ms}ms)")
            return {"status": "ok"}
    except ValueError:
        log.warning(f"Invalid timestamp from {email}")
        raise HTTPException(status_code=400, detail="Invalid form data")

    # Spam check 3: Turnstile verification (production only)
    if settings.turnstile_secret and not verify_turnstile(cf_turnstile_response):
        log.info(f"Turnstile verification failed from {email}")
        return {"status": "ok"}

    log.info(f"Contact form submitted: {name} <{email}> - {subject or 'No subject'}")

    # Format message for Telegram
    subject_text = subject if subject else "No subject"
    telegram_message = f"""**From:** {name} <{email}>
**Subject:** {subject_text}
**Message:**
{message}"""

    send_telegram_message(telegram_message)

    return {"status": "ok", "message": "Message sent successfully"}
