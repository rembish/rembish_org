"""Telegram webhook endpoint for drone flight record uploads."""

from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..log_config import get_logger
from .processing import process_flight_record

log = get_logger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _reply(chat_id: int, reply_to: int, text: str) -> None:
    """Send a reply message to a Telegram chat."""
    token = settings.telegram_token
    if not token:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = httpx.post(
            url,
            json={"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to},
        )
        if not resp.is_success:
            log.warning("Telegram sendMessage failed: %s %s", resp.status_code, resp.text)
    except Exception:
        log.warning("Failed to send Telegram reply", exc_info=True)


def _download_file(file_id: str) -> bytes:
    """Download a file from Telegram by file_id."""
    token = settings.telegram_token
    # Get file path
    resp = httpx.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}")
    resp.raise_for_status()
    file_path = resp.json()["result"]["file_path"]
    # Download file content
    dl_resp = httpx.get(f"https://api.telegram.org/file/bot{token}/{file_path}")
    dl_resp.raise_for_status()
    return dl_resp.content


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict[str, str]:
    """Handle incoming Telegram webhook updates."""
    # Verify webhook secret
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            log.warning("Telegram webhook: invalid secret token")
            return {"status": "ok"}

    body: dict[str, Any] = await request.json()
    message: dict[str, Any] | None = body.get("message")
    if not message:
        return {"status": "ok"}

    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id", 0)

    # Only accept messages from the configured admin chat
    if str(chat_id) != settings.telegram_chat_id:
        log.info("Telegram webhook: ignoring message from chat %s", chat_id)
        return {"status": "ok"}

    document = message.get("document")
    if not document:
        _reply(chat_id, message_id, "Send me a DJI flight record .txt file")
        return {"status": "ok"}

    filename: str = document.get("file_name", "")
    if not filename.lower().endswith(".txt"):
        _reply(chat_id, message_id, "Only .txt flight record files are supported")
        return {"status": "ok"}

    # Download and process
    try:
        file_data = _download_file(document["file_id"])
    except Exception:
        log.error("Telegram webhook: failed to download file %s", filename, exc_info=True)
        _reply(chat_id, message_id, f"Failed to download file: {filename}")
        return {"status": "ok"}

    try:
        result = process_flight_record(file_data, filename, db)
        _reply(chat_id, message_id, result)
        log.info("Telegram webhook: processed %s — %s", filename, result.split("\n")[0])
    except Exception:
        log.error("Telegram webhook: failed to process %s", filename, exc_info=True)
        db.rollback()
        _reply(chat_id, message_id, f"Error processing {filename}. Check server logs.")

    return {"status": "ok"}
