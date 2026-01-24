import os
import time
import httpx
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr

app = FastAPI(title="rembish.org API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Spam protection settings
MIN_SUBMISSION_TIME_MS = 3000  # Reject forms submitted faster than 3 seconds


def send_telegram_message(text: str) -> bool:
    """Send message to Telegram chat."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        # Telegram not configured, skip silently in dev
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = httpx.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    })
    return response.is_success


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/info")
def info():
    return {
        "name": "rembish.org",
        "version": "0.1.0",
    }


@app.post("/api/v1/contact")
def contact(
    name: str = Form(..., min_length=2),
    email: EmailStr = Form(...),
    subject: str = Form(""),
    message: str = Form(..., min_length=10),
    website: str = Form(""),  # Honeypot
    ts: str = Form("0"),  # Timestamp when form was loaded
):
    # Spam check 1: Honeypot field should be empty
    if website:
        # Pretend success to not reveal detection
        return {"status": "ok"}

    # Spam check 2: Form submitted too quickly
    try:
        loaded_ts = int(ts)
        elapsed_ms = int(time.time() * 1000) - loaded_ts
        if elapsed_ms < MIN_SUBMISSION_TIME_MS:
            # Pretend success to not reveal detection
            return {"status": "ok"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid form data")

    # Format message for Telegram
    subject_text = subject if subject else "No subject"
    telegram_message = f"""**From:** {name} <{email}>
**Subject:** {subject_text}
**Message:**
{message}"""

    send_telegram_message(telegram_message)

    return {"status": "ok", "message": "Message sent successfully"}
