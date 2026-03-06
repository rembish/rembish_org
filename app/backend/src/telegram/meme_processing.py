"""Process meme images received via Telegram."""

import io
import uuid
from typing import Any

from sqlalchemy.orm import Session

from ..extraction import extract_meme_metadata
from ..log_config import get_logger
from ..models.meme import Meme
from ..storage import get_storage

log = get_logger(__name__)

IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _get_dimensions(file_data: bytes) -> tuple[int | None, int | None]:
    """Get image dimensions using PIL."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(file_data))
        return img.width, img.height
    except Exception:
        log.warning("Failed to get image dimensions", exc_info=True)
        return None, None


def _extract_source_url(message: dict[str, Any]) -> str | None:
    """Extract source URL from forwarded message or caption."""
    # Check caption for URLs
    caption: str | None = message.get("caption")
    if caption:
        for word in caption.split():
            if word.startswith(("http://", "https://")):
                return word

    # Check forward_origin for channel attribution
    forward_origin: dict[str, Any] | None = message.get("forward_origin")
    if forward_origin:
        chat = forward_origin.get("chat")
        if chat and chat.get("username"):
            return f"https://t.me/{chat['username']}"

    return None


def process_meme(
    file_data: bytes,
    mime_type: str,
    message: dict[str, Any],
    db: Session,
    *,
    is_test: bool = False,
) -> str:
    """Process a meme image: save, run AI triage, insert DB record.

    Returns a reply message string.
    """
    message_id = message.get("message_id", 0)

    # Dedup by telegram_message_id
    if message_id:
        existing = db.query(Meme).filter(Meme.telegram_message_id == message_id).first()
        if existing:
            return "Already processed this meme."

    # Save image to storage
    ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(mime_type, ".jpg")
    filename = f"{uuid.uuid4().hex}{ext}"

    storage = get_storage("memes")
    media_path = storage.save(filename, file_data, content_type=mime_type)

    # Get dimensions
    width, height = _get_dimensions(file_data)

    # AI triage
    result = extract_meme_metadata(file_data, mime_type)
    language = None
    category = None
    description_en = None
    is_site_worthy = None
    ai_note = ""

    if result.meme:
        language = result.meme.language
        category = result.meme.category
        description_en = result.meme.description_en
        is_site_worthy = result.meme.is_site_worthy
        worthy_str = "yes" if is_site_worthy else "no"
        ai_note = f"\nAI: {category}/{language}, site-worthy: {worthy_str}"
    elif result.error:
        ai_note = f"\nAI extraction failed: {result.error}"

    # Extract source URL
    source_url = _extract_source_url(message)

    # Insert DB record
    meme = Meme(
        status="pending",
        source_type="telegram",
        source_url=source_url,
        media_path=media_path,
        mime_type=mime_type,
        width=width,
        height=height,
        language=language,
        category=category,
        description_en=description_en,
        is_site_worthy=is_site_worthy,
        telegram_message_id=message_id,
        is_test=is_test,
    )
    db.add(meme)
    db.commit()
    db.refresh(meme)

    log.info("Meme saved: id=%d, category=%s, language=%s", meme.id, category, language)
    return f"Meme saved (pending review).{ai_note}"
