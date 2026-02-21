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


FLIGHT_EXTRACTION_PROMPT = """\
You are a flight ticket data extractor. \
Analyze this document (boarding pass, e-ticket, itinerary) and extract all flights.

Return ONLY a JSON array of flight objects. Each flight should have these fields \
(use null for unknown values):
{
  "flight_date": "YYYY-MM-DD (departure date)",
  "flight_number": "e.g. TK1770, LH900",
  "airline_name": "full airline name",
  "departure_iata": "3-letter IATA code",
  "arrival_iata": "3-letter IATA code",
  "departure_time": "HH:MM (24h local time)",
  "arrival_time": "HH:MM (24h local time)",
  "arrival_date": "YYYY-MM-DD only if different from flight_date (overnight), else null",
  "terminal": "departure terminal or null",
  "arrival_terminal": "arrival terminal or null",
  "aircraft_type": "e.g. Boeing 737-800, Airbus A321neo, or null",
  "seat": "e.g. 14A, or null",
  "booking_reference": "PNR/confirmation code, or null"
}

Rules:
- Return a JSON array even for a single flight: [{"flight_date": ...}]
- For multi-leg itineraries, return one object per leg
- Use IATA airport codes (3 letters), not ICAO
- Use 24-hour time format
- Extract booking/confirmation/PNR reference if visible
- If the document is not a flight ticket, return an empty array: []"""


class ExtractedFlight(BaseModel):
    flight_date: str | None = None
    flight_number: str | None = None
    airline_name: str | None = None
    departure_iata: str | None = None
    arrival_iata: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    arrival_date: str | None = None
    terminal: str | None = None
    arrival_terminal: str | None = None
    aircraft_type: str | None = None
    seat: str | None = None
    booking_reference: str | None = None


class FlightExtractionResult(BaseModel):
    flights: list[ExtractedFlight] | None = None
    error: str | None = None


CAR_RENTAL_EXTRACTION_PROMPT = """\
You are a car rental reservation data extractor. \
Analyze this document (reservation confirmation, booking receipt) and extract rental details.

Return ONLY a JSON object with these fields (use null for unknown values):
{
  "rental_company": "company name, e.g. Hertz, Europcar, Sixt",
  "car_class": "vehicle class/category, e.g. Economy, Compact SUV, Full Size",
  "transmission": "manual" or "automatic" or null,
  "pickup_location": "pickup location/office name",
  "dropoff_location": "drop-off location (same as pickup if one-way not mentioned)",
  "pickup_datetime": "YYYY-MM-DD HH:MM",
  "dropoff_datetime": "YYYY-MM-DD HH:MM",
  "is_paid": true if prepaid/already charged, false if pay-on-pickup,
  "total_amount": "amount with currency symbol, e.g. €245.00, $189.50",
  "confirmation_number": "reservation/confirmation/booking number, or null",
  "notes": "important details like cancellation policy, insurance, extras"
}

Rules:
- Extract the rental company name as it appears on the document
- For car_class, use the category name (Economy, Compact, etc.), not a specific car model
- Use 24-hour time format for pickup/dropoff times
- Include currency symbol in total_amount
- Keep notes concise but include cancellation terms if visible
- If the document is not a car rental reservation, return all null values"""


class ExtractedCarRental(BaseModel):
    rental_company: str | None = None
    car_class: str | None = None
    transmission: str | None = None
    pickup_location: str | None = None
    dropoff_location: str | None = None
    pickup_datetime: str | None = None
    dropoff_datetime: str | None = None
    is_paid: bool | None = None
    total_amount: str | None = None
    confirmation_number: str | None = None
    notes: str | None = None


class CarRentalExtractionResult(BaseModel):
    rental: ExtractedCarRental | None = None
    error: str | None = None


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


def extract_flight_data(file_content: bytes, mime_type: str) -> FlightExtractionResult:
    """Extract flight data from a PDF or image using Claude Haiku."""
    if not settings.anthropic_api_key:
        return FlightExtractionResult(error="API key not configured")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

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
            return FlightExtractionResult(error=f"Unsupported file type: {mime_type}")

        content.append({"type": "text", "text": FLIGHT_EXTRACTION_PROMPT})

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": content}],  # type: ignore[typeddict-item]
        )

        text = response.content[0].text.strip()  # type: ignore[union-attr]

        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        data = json.loads(text)
        if not isinstance(data, list):
            data = [data]
        flights = [ExtractedFlight(**f) for f in data]
        return FlightExtractionResult(flights=flights)

    except json.JSONDecodeError:
        log.warning("Failed to parse flight extraction response as JSON")
        return FlightExtractionResult(error="Failed to parse AI response")
    except Exception as exc:
        log.exception("Flight data extraction failed")
        msg = str(exc)
        if "credit" in msg.lower() or "balance" in msg.lower() or "402" in msg:
            return FlightExtractionResult(error="Insufficient API balance")
        if "401" in msg or "auth" in msg.lower():
            return FlightExtractionResult(error="Invalid API key")
        return FlightExtractionResult(error="Extraction failed")


def extract_car_rental_data(file_content: bytes, mime_type: str) -> CarRentalExtractionResult:
    """Extract car rental data from a PDF or image using Claude Haiku."""
    if not settings.anthropic_api_key:
        return CarRentalExtractionResult(error="API key not configured")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

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
            return CarRentalExtractionResult(error=f"Unsupported file type: {mime_type}")

        content.append({"type": "text", "text": CAR_RENTAL_EXTRACTION_PROMPT})

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],  # type: ignore[typeddict-item]
        )

        text = response.content[0].text.strip()  # type: ignore[union-attr]

        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        data = json.loads(text)
        return CarRentalExtractionResult(rental=ExtractedCarRental(**data))

    except json.JSONDecodeError:
        log.warning("Failed to parse car rental extraction response as JSON")
        return CarRentalExtractionResult(error="Failed to parse AI response")
    except Exception as exc:
        log.exception("Car rental data extraction failed")
        msg = str(exc)
        if "credit" in msg.lower() or "balance" in msg.lower() or "402" in msg:
            return CarRentalExtractionResult(error="Insufficient API balance")
        if "401" in msg or "auth" in msg.lower():
            return CarRentalExtractionResult(error="Invalid API key")
        return CarRentalExtractionResult(error="Extraction failed")
