"""AI-powered metadata extraction from travel document PDFs/images."""

import base64
import json
import re
from typing import Any

from pydantic import BaseModel

from .config import settings
from .log_config import get_logger

log = get_logger(__name__)

EXTRACTION_PROMPT = """\
You are a travel document metadata extractor. \
Analyze this document and extract structured metadata.

Return ONLY a JSON object with these fields (use null for unknown values):
{
  "doc_type": one of "e_visa", "eta", "esta", "etias", "loi", \
"entry_permit", "travel_insurance", "vaccination_cert", "other",
  "label": "short descriptive label, e.g. 'India e-Visa' or 'UK ETA'",
  "country_code": "ISO alpha-2 country code, e.g. 'IN', 'GB'",
  "valid_from": "YYYY-MM-DD or null",
  "valid_until": "YYYY-MM-DD or null",
  "entry_type": "single" | "double" | "multiple" | null,
  "notes": "visa/reference number, conditions, or other important details",
  "passport_number": "passport number mentioned in the document, or null"
}

Rules:
- For e-visas, ETAs, ESTAs: extract validity dates and entry type
- For travel insurance: extract coverage period
- For vaccination certificates: extract vaccine type and date
- Country code should be the destination country, not issuing country
- Keep notes concise but include reference/application numbers
- Extract the passport/travel document number the visa was issued against, if visible"""


class ExtractedDocMetadata(BaseModel):
    doc_type: str | None = None
    label: str | None = None
    country_code: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    entry_type: str | None = None
    notes: str | None = None
    passport_number: str | None = None


class ExtractionResult(BaseModel):
    metadata: ExtractedDocMetadata | None = None
    error: str | None = None


def extract_document_metadata(file_content: bytes, mime_type: str) -> ExtractionResult:
    """Extract metadata from a PDF or image using Claude Haiku."""
    if not settings.anthropic_api_key:
        return ExtractionResult(error="API key not configured")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Build content based on mime type
        content: list[dict[str, Any]] = []
        if mime_type == "application/pdf":
            content.append(
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.b64encode(file_content).decode(),
                    },
                }
            )
        elif mime_type.startswith("image/"):
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": base64.b64encode(file_content).decode(),
                    },
                }
            )
        else:
            return ExtractionResult(error=f"Unsupported file type: {mime_type}")

        content.append({"type": "text", "text": EXTRACTION_PROMPT})

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],  # type: ignore[typeddict-item]
        )

        # Parse response text
        text = response.content[0].text.strip()  # type: ignore[union-attr]

        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        data = json.loads(text)
        return ExtractionResult(metadata=ExtractedDocMetadata(**data))

    except json.JSONDecodeError:
        log.warning("Failed to parse extraction response as JSON")
        return ExtractionResult(error="Failed to parse AI response")
    except Exception as exc:
        log.exception("Document metadata extraction failed")
        msg = str(exc)
        if "credit" in msg.lower() or "balance" in msg.lower() or "402" in msg:
            return ExtractionResult(error="Insufficient API balance")
        if "401" in msg or "auth" in msg.lower():
            return ExtractionResult(error="Invalid API key")
        return ExtractionResult(error="Extraction failed")
