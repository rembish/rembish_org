"""Tests for AI document metadata extraction."""

import json
from unittest.mock import MagicMock, patch

from src.extraction import ExtractionResult, extract_document_metadata, extract_flight_data


@patch("src.extraction.settings")
def test_extract_disabled_without_api_key(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = ""
    result = extract_document_metadata(b"data", "application/pdf")
    assert result.error == "API key not configured"
    assert result.metadata is None


@patch("src.extraction.settings")
def test_extract_unsupported_mime_type(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"
    result = extract_document_metadata(b"data", "text/plain")
    assert result.error is not None
    assert "Unsupported" in result.error


@patch("src.extraction.settings")
def test_extract_image_success(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = '{"doc_type": "eta", "label": "UK ETA", "country_code": "GB"}'
    mock_response.content = [mock_content_block]

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = extract_document_metadata(b"image-data", "image/jpeg")
        assert result.metadata is not None
        assert result.metadata.doc_type == "eta"
        assert result.metadata.country_code == "GB"


@patch("src.extraction.settings")
def test_extract_pdf_with_code_fences(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = '```json\n{"doc_type": "e_visa", "label": "India e-Visa"}\n```'
    mock_response.content = [mock_content_block]

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = extract_document_metadata(b"pdf-data", "application/pdf")
        assert result.metadata is not None
        assert result.metadata.doc_type == "e_visa"


@patch("src.extraction.settings")
def test_extract_invalid_json(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = "This is not JSON"
    mock_response.content = [mock_content_block]

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = extract_document_metadata(b"data", "application/pdf")
        assert result.error == "Failed to parse AI response"


@patch("src.extraction.settings")
def test_extract_api_error(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Connection refused")
        mock_cls.return_value = mock_client

        result = extract_document_metadata(b"data", "application/pdf")
        assert result.error == "Extraction failed"


@patch("src.extraction.settings")
def test_extract_insufficient_balance(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("402 insufficient credit balance")
        mock_cls.return_value = mock_client

        result = extract_document_metadata(b"data", "application/pdf")
        assert result.error == "Insufficient API balance"


@patch("src.extraction.settings")
def test_extract_invalid_key(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("401 authentication failed")
        mock_cls.return_value = mock_client

        result = extract_document_metadata(b"data", "application/pdf")
        assert result.error == "Invalid API key"


# --- Flight extraction tests ---


@patch("src.extraction.settings")
def test_extract_flights_disabled_without_api_key(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = ""
    result = extract_flight_data(b"data", "application/pdf")
    assert result.error == "API key not configured"
    assert result.flights is None


@patch("src.extraction.settings")
def test_extract_flights_unsupported_mime(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"
    result = extract_flight_data(b"data", "text/plain")
    assert result.error is not None
    assert "Unsupported" in result.error


@patch("src.extraction.settings")
def test_extract_flights_single_leg(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    flight_data = [
        {
            "flight_date": "2026-03-10",
            "flight_number": "TK1770",
            "airline_name": "Turkish Airlines",
            "departure_iata": "PRG",
            "arrival_iata": "IST",
            "departure_time": "06:30",
            "arrival_time": "10:15",
        }
    ]

    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = json.dumps(flight_data)
    mock_response.content = [mock_content_block]

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = extract_flight_data(b"pdf-data", "application/pdf")
        assert result.flights is not None
        assert len(result.flights) == 1
        assert result.flights[0].flight_number == "TK1770"
        assert result.flights[0].departure_iata == "PRG"


@patch("src.extraction.settings")
def test_extract_flights_multi_leg(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    flight_data = [
        {
            "flight_date": "2026-03-10",
            "flight_number": "TK1770",
            "departure_iata": "PRG",
            "arrival_iata": "IST",
        },
        {
            "flight_date": "2026-03-10",
            "flight_number": "TK700",
            "departure_iata": "IST",
            "arrival_iata": "JFK",
        },
    ]

    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = json.dumps(flight_data)
    mock_response.content = [mock_content_block]

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = extract_flight_data(b"pdf-data", "application/pdf")
        assert result.flights is not None
        assert len(result.flights) == 2
        assert result.flights[0].flight_number == "TK1770"
        assert result.flights[1].flight_number == "TK700"


@patch("src.extraction.settings")
def test_extract_flights_with_code_fences(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    flight_data = [
        {
            "flight_date": "2026-03-10",
            "flight_number": "LH900",
            "departure_iata": "FRA",
            "arrival_iata": "JFK",
        }
    ]

    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = f"```json\n{json.dumps(flight_data)}\n```"
    mock_response.content = [mock_content_block]

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = extract_flight_data(b"image-data", "image/jpeg")
        assert result.flights is not None
        assert len(result.flights) == 1
        assert result.flights[0].flight_number == "LH900"


@patch("src.extraction.settings")
def test_extract_flights_invalid_json(mock_settings: MagicMock) -> None:
    mock_settings.anthropic_api_key = "test-key"

    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = "Sorry, I cannot read this document"
    mock_response.content = [mock_content_block]

    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        result = extract_flight_data(b"data", "application/pdf")
        assert result.error == "Failed to parse AI response"
