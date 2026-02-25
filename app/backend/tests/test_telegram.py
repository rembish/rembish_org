"""Tests for Telegram webhook and flight record processing."""

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Drone, DroneFlight


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------


def test_webhook_no_message(client: TestClient) -> None:
    resp = client.post("/api/v1/telegram/webhook", json={})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_webhook_wrong_chat(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"chat": {"id": 99999}, "message_id": 1}},
    )
    assert resp.status_code == 200


@patch("src.telegram.webhook.settings")
@patch("src.telegram.webhook._reply")
def test_webhook_no_document(mock_reply: MagicMock, mock_settings: MagicMock, client: TestClient) -> None:
    mock_settings.telegram_webhook_secret = ""
    mock_settings.telegram_chat_id = "12345"
    mock_settings.telegram_token = "test-token"
    resp = client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"chat": {"id": 12345}, "message_id": 1, "text": "hello"}},
    )
    assert resp.status_code == 200
    mock_reply.assert_called_once()
    assert "Send me a DJI flight record" in mock_reply.call_args[0][2]


@patch("src.telegram.webhook.settings")
@patch("src.telegram.webhook._reply")
def test_webhook_wrong_extension(mock_reply: MagicMock, mock_settings: MagicMock, client: TestClient) -> None:
    mock_settings.telegram_webhook_secret = ""
    mock_settings.telegram_chat_id = "12345"
    mock_settings.telegram_token = "test-token"
    resp = client.post(
        "/api/v1/telegram/webhook",
        json={
            "message": {
                "chat": {"id": 12345},
                "message_id": 1,
                "document": {"file_name": "photo.jpg", "file_id": "abc"},
            }
        },
    )
    assert resp.status_code == 200
    mock_reply.assert_called_once()
    assert ".txt" in mock_reply.call_args[0][2]


@patch("src.telegram.webhook.settings")
@patch("src.telegram.webhook._reply")
def test_webhook_secret_mismatch(mock_reply: MagicMock, mock_settings: MagicMock, client: TestClient) -> None:
    mock_settings.telegram_webhook_secret = "real-secret"
    resp = client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"chat": {"id": 12345}, "message_id": 1}},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
    )
    assert resp.status_code == 200
    mock_reply.assert_not_called()


@patch("src.telegram.webhook.settings")
@patch("src.telegram.webhook._reply")
@patch("src.telegram.webhook._download_file", side_effect=Exception("network error"))
def test_webhook_download_fails(
    mock_dl: MagicMock, mock_reply: MagicMock, mock_settings: MagicMock, client: TestClient
) -> None:
    mock_settings.telegram_webhook_secret = ""
    mock_settings.telegram_chat_id = "12345"
    mock_settings.telegram_token = "test-token"
    resp = client.post(
        "/api/v1/telegram/webhook",
        json={
            "message": {
                "chat": {"id": 12345},
                "message_id": 1,
                "document": {"file_name": "DJIFlightRecord_2025-01-01_[12-00-00].txt", "file_id": "abc"},
            }
        },
    )
    assert resp.status_code == 200
    mock_reply.assert_called_once()
    assert "Failed to download" in mock_reply.call_args[0][2]


# ---------------------------------------------------------------------------
# CSRF exemption
# ---------------------------------------------------------------------------


def test_webhook_no_csrf_required(client: TestClient) -> None:
    """Webhook should work without X-CSRF header."""
    with TestClient(client.app) as no_csrf_client:
        resp = no_csrf_client.post("/api/v1/telegram/webhook", json={})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def test_processing_dedup(db_session: Session) -> None:
    """process_flight_record skips if source_file already exists."""
    from src.telegram.processing import process_flight_record

    # Pre-create a flight with the same source_file
    drone = Drone(name="test.drone", model="Test")
    db_session.add(drone)
    db_session.flush()
    existing = DroneFlight(
        drone_id=drone.id,
        flight_date=date(2025, 1, 1),
        source_file="DJIFlightRecord_2025-01-01_[12-00-00]",
    )
    db_session.add(existing)
    db_session.commit()

    # Mock the DJI log parsing to return dummy data
    with patch("src.telegram.processing.DJILog") as mock_log_cls:
        mock_log = MagicMock()
        mock_log.version = 6
        mock_log.details = MagicMock()
        mock_log.frames.return_value = []
        mock_log_cls.from_bytes.return_value = mock_log

        with patch("src.telegram.processing.FrameDetails") as mock_fd_cls:
            mock_fd = MagicMock()
            mock_fd.latitude = 50.0
            mock_fd.longitude = 14.0
            mock_fd.total_time = 120.0
            mock_fd.total_distance = 500.0
            mock_fd.max_horizontal_speed = 10.0
            mock_fd.photo_num = 0
            mock_fd.video_time = 0.0
            mock_fd_cls.from_details.return_value = mock_fd

            result = process_flight_record(
                b"fake-data", "DJIFlightRecord_2025-01-01_[12-00-00].txt", db_session
            )
            assert "Already imported" in result


def test_processing_no_date() -> None:
    """process_flight_record returns error if date can't be determined."""
    from src.telegram.processing import process_flight_record

    db = MagicMock()

    with patch("src.telegram.processing.DJILog") as mock_log_cls:
        mock_log = MagicMock()
        mock_log.version = 6
        mock_log.frames.return_value = []
        mock_log_cls.from_bytes.return_value = mock_log

        with patch("src.telegram.processing.FrameDetails") as mock_fd_cls:
            mock_fd = MagicMock()
            mock_fd.latitude = 50.0
            mock_fd.longitude = 14.0
            mock_fd.total_time = 120.0
            mock_fd.total_distance = 500.0
            mock_fd.max_horizontal_speed = 10.0
            mock_fd.photo_num = 0
            mock_fd.video_time = 0.0
            mock_fd_cls.from_details.return_value = mock_fd

            result = process_flight_record(b"fake-data", "random_file.txt", db)
            assert "Could not determine flight date" in result


# ---------------------------------------------------------------------------
# RDP simplification
# ---------------------------------------------------------------------------


def test_rdp_simplify_short_list() -> None:
    from src.telegram.processing import _rdp_simplify

    coords = [[0.0, 0.0], [1.0, 1.0]]
    assert _rdp_simplify(coords, 0.001) == coords


def test_rdp_simplify_collinear() -> None:
    from src.telegram.processing import _rdp_simplify

    coords = [[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]]
    result = _rdp_simplify(coords, 0.001)
    assert len(result) == 2


def test_rdp_simplify_preserves_deviation() -> None:
    from src.telegram.processing import _rdp_simplify

    coords = [[0.0, 0.0], [0.5, 1.0], [1.0, 0.0]]
    result = _rdp_simplify(coords, 0.001)
    assert len(result) == 3


# ---------------------------------------------------------------------------
# Trip matching
# ---------------------------------------------------------------------------


def test_find_trip_bounded(db_session: Session) -> None:
    from datetime import date

    from src.models import Trip
    from src.telegram.processing import _find_trip

    trip = Trip(start_date=date(2025, 6, 1), end_date=date(2025, 6, 15), trip_type="regular")
    db_session.add(trip)
    db_session.commit()

    assert _find_trip(db_session, date(2025, 6, 5)) is not None
    assert _find_trip(db_session, date(2025, 7, 1)) is None


def test_find_trip_open_ended(db_session: Session) -> None:
    from datetime import date

    from src.models import Trip
    from src.telegram.processing import _find_trip

    trip = Trip(start_date=date(2025, 1, 1), end_date=None, trip_type="regular")
    db_session.add(trip)
    db_session.commit()

    assert _find_trip(db_session, date(2025, 6, 5)) is not None
    assert _find_trip(db_session, date(2024, 12, 31)) is None
