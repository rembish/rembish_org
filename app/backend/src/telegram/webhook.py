"""Telegram webhook endpoint for drone flight records and meme uploads."""

from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..log_config import get_logger
from .meme_processing import IMAGE_MIME_TYPES, process_meme
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


def _handle_drone_document(
    document: dict[str, Any],
    message: dict[str, Any],
    chat_id: int,
    message_id: int,
    db: Session,
) -> None:
    """Process a .txt DJI flight record document."""
    filename: str = document.get("file_name", "")
    try:
        file_data = _download_file(document["file_id"])
    except Exception:
        log.error("Telegram webhook: failed to download file %s", filename, exc_info=True)
        _reply(chat_id, message_id, f"Failed to download file: {filename}")
        return

    try:
        result = process_flight_record(file_data, filename, db)
        _reply(chat_id, message_id, result)
        log.info("Telegram webhook: processed %s — %s", filename, result.split("\n")[0])
    except Exception:
        log.error("Telegram webhook: failed to process %s", filename, exc_info=True)
        db.rollback()
        _reply(chat_id, message_id, f"Error processing {filename}. Check server logs.")


def _handle_meme_photo(
    file_id: str,
    mime_type: str,
    message: dict[str, Any],
    chat_id: int,
    message_id: int,
    db: Session,
) -> None:
    """Download and process a meme image."""
    try:
        file_data = _download_file(file_id)
    except Exception:
        log.error("Telegram webhook: failed to download meme photo", exc_info=True)
        _reply(chat_id, message_id, "Failed to download image.")
        return

    try:
        result = process_meme(file_data, mime_type, message, db)
        _reply(chat_id, message_id, result)
    except Exception:
        log.error("Telegram webhook: failed to process meme", exc_info=True)
        db.rollback()
        _reply(chat_id, message_id, "Error processing meme. Check server logs.")


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

    # Route 1: Photo array (compressed images from Telegram)
    photos: list[dict[str, Any]] | None = message.get("photo")
    if photos:
        # Telegram sends multiple sizes; pick the largest (last in array)
        best_photo = photos[-1]
        _handle_meme_photo(best_photo["file_id"], "image/jpeg", message, chat_id, message_id, db)
        return {"status": "ok"}

    # Route 2: Document
    document = message.get("document")
    if document:
        filename: str = document.get("file_name", "")
        doc_mime: str = document.get("mime_type", "")

        # .txt → drone flight record
        if filename.lower().endswith(".txt"):
            _handle_drone_document(document, message, chat_id, message_id, db)
            return {"status": "ok"}

        # Image document (sent as file, uncompressed) → meme
        if doc_mime in IMAGE_MIME_TYPES:
            _handle_meme_photo(document["file_id"], doc_mime, message, chat_id, message_id, db)
            return {"status": "ok"}

        _reply(
            chat_id,
            message_id,
            "Send me a DJI .txt flight record or a meme image.",
        )
        return {"status": "ok"}

    _reply(chat_id, message_id, "Send me a DJI .txt flight record or a meme image.")
    return {"status": "ok"}
