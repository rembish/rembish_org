"""Tests for meme admin endpoints, meme processing, and meme upload."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.meme import Meme


# ---------------------------------------------------------------------------
# Admin meme endpoints
# ---------------------------------------------------------------------------


def _create_meme(db: Session, **overrides: object) -> Meme:
    defaults = {
        "status": "pending",
        "source_type": "telegram",
        "media_path": "/app/data/memes/test.jpg",
        "mime_type": "image/jpeg",
        "language": "en",
        "category": "dev",
        "description_en": "A test meme",
        "is_site_worthy": True,
        "telegram_message_id": None,
    }
    defaults.update(overrides)
    meme = Meme(**defaults)  # type: ignore[arg-type]
    db.add(meme)
    db.commit()
    db.refresh(meme)
    return meme


def test_meme_stats(admin_client: TestClient, db_session: Session) -> None:
    _create_meme(db_session, status="pending")
    _create_meme(db_session, status="pending", media_path="/app/data/memes/b.jpg")
    _create_meme(db_session, status="approved", media_path="/app/data/memes/c.jpg")

    resp = admin_client.get("/api/v1/admin/memes/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pending"] == 2
    assert data["approved"] == 1
    assert data["rejected"] == 0
    assert data["total"] == 3


def test_meme_list_default_pending(admin_client: TestClient, db_session: Session) -> None:
    _create_meme(db_session, status="pending")
    _create_meme(db_session, status="approved", media_path="/app/data/memes/b.jpg")

    resp = admin_client.get("/api/v1/admin/memes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["memes"][0]["status"] == "pending"


def test_meme_list_all(admin_client: TestClient, db_session: Session) -> None:
    _create_meme(db_session, status="pending")
    _create_meme(db_session, status="approved", media_path="/app/data/memes/b.jpg")

    resp = admin_client.get("/api/v1/admin/memes?status=")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2


def test_meme_get(admin_client: TestClient, db_session: Session) -> None:
    meme = _create_meme(db_session)
    resp = admin_client.get(f"/api/v1/admin/memes/{meme.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == meme.id


def test_meme_get_not_found(admin_client: TestClient) -> None:
    resp = admin_client.get("/api/v1/admin/memes/99999")
    assert resp.status_code == 404


def test_meme_approve(admin_client: TestClient, db_session: Session) -> None:
    meme = _create_meme(db_session)
    resp = admin_client.post(
        f"/api/v1/admin/memes/{meme.id}/approve",
        json={"category": "math"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["category"] == "math"
    assert data["approved_at"] is not None


def test_meme_reject(admin_client: TestClient, db_session: Session) -> None:
    meme = _create_meme(db_session)
    resp = admin_client.post(
        f"/api/v1/admin/memes/{meme.id}/reject",
        json={},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_meme_update(admin_client: TestClient, db_session: Session) -> None:
    meme = _create_meme(db_session)
    resp = admin_client.put(
        f"/api/v1/admin/memes/{meme.id}",
        json={"language": "ru", "description_en": "Updated desc"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "ru"
    assert data["description_en"] == "Updated desc"


def test_meme_admin_required(client: TestClient) -> None:
    """Meme endpoints require admin auth."""
    resp = client.get("/api/v1/admin/memes/stats")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Meme processing
# ---------------------------------------------------------------------------


def test_process_meme_dedup(db_session: Session) -> None:
    """process_meme skips if telegram_message_id already exists."""
    _create_meme(db_session, telegram_message_id=42)

    from src.telegram.meme_processing import process_meme

    result = process_meme(
        b"fake-data",
        "image/jpeg",
        {"message_id": 42},
        db_session,
    )
    assert "Already processed" in result


@patch("src.telegram.meme_processing.extract_meme_metadata")
@patch("src.telegram.meme_processing.get_storage")
def test_process_meme_saves(mock_storage_fn: MagicMock, mock_extract: MagicMock, db_session: Session) -> None:
    """process_meme saves the image and creates a DB record."""
    from src.extraction import ExtractedMeme, MemeExtractionResult
    from src.telegram.meme_processing import process_meme

    mock_storage = MagicMock()
    mock_storage.save.return_value = "/app/data/memes/abc.jpg"
    mock_storage_fn.return_value = mock_storage

    mock_extract.return_value = MemeExtractionResult(
        meme=ExtractedMeme(language="en", category="dev", description_en="Test", is_site_worthy=True)
    )

    with patch("src.telegram.meme_processing._get_dimensions", return_value=(800, 600)):
        result = process_meme(
            b"fake-image-data",
            "image/jpeg",
            {"message_id": 100},
            db_session,
        )

    assert "Meme saved" in result
    assert "dev/en" in result
    assert "site-worthy: yes" in result

    meme = db_session.query(Meme).filter(Meme.telegram_message_id == 100).first()
    assert meme is not None
    assert meme.status == "pending"
    assert meme.language == "en"
    assert meme.category == "dev"
    assert meme.width == 800
    assert meme.height == 600


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


@patch("src.extraction.settings")
def test_meme_extraction_no_api_key(mock_settings: MagicMock) -> None:
    from src.extraction import extract_meme_metadata

    mock_settings.anthropic_api_key = ""
    result = extract_meme_metadata(b"data", "image/jpeg")
    assert result.error == "API key not configured"


@patch("src.extraction.settings")
def test_meme_extraction_unsupported_type(mock_settings: MagicMock) -> None:
    from src.extraction import extract_meme_metadata

    mock_settings.anthropic_api_key = "test-key"
    result = extract_meme_metadata(b"data", "application/pdf")
    assert result.error is not None
    assert "Unsupported" in result.error


# ---------------------------------------------------------------------------
# Source URL extraction
# ---------------------------------------------------------------------------


def test_extract_source_url_from_caption() -> None:
    from src.telegram.meme_processing import _extract_source_url

    msg = {"caption": "Check this out https://example.com/meme.jpg"}
    assert _extract_source_url(msg) == "https://example.com/meme.jpg"


def test_extract_source_url_from_forward() -> None:
    from src.telegram.meme_processing import _extract_source_url

    msg = {"forward_origin": {"chat": {"username": "memechannel"}}}
    assert _extract_source_url(msg) == "https://t.me/memechannel"


def test_extract_source_url_none() -> None:
    from src.telegram.meme_processing import _extract_source_url

    assert _extract_source_url({}) is None


# ---------------------------------------------------------------------------
# Meme upload endpoint
# ---------------------------------------------------------------------------


def test_upload_meme_requires_auth(client: TestClient) -> None:
    """Upload endpoint requires admin auth."""
    resp = client.post(
        "/api/v1/admin/memes/upload",
        files={"file": ("meme.jpg", b"data", "image/jpeg")},
    )
    assert resp.status_code == 401


def test_upload_meme_rejects_non_image(admin_client: TestClient) -> None:
    """Upload rejects non-image files."""
    resp = admin_client.post(
        "/api/v1/admin/memes/upload",
        files={"file": ("doc.pdf", b"data", "application/pdf")},
    )
    assert resp.status_code == 400
    assert "image" in resp.json()["detail"]


def test_upload_meme_rejects_empty(admin_client: TestClient) -> None:
    """Upload rejects empty files."""
    resp = admin_client.post(
        "/api/v1/admin/memes/upload",
        files={"file": ("meme.jpg", b"", "image/jpeg")},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"]


@patch("src.admin.memes.process_meme")
def test_upload_meme_success(
    mock_process: MagicMock, admin_client: TestClient, db_session: Session
) -> None:
    """Successful upload creates meme with source_type='upload'."""

    def _fake_process(
        file_data: bytes,
        mime_type: str,
        message: dict[str, object],
        db: Session,
        **kwargs: object,
    ) -> str:
        meme = Meme(
            status="pending",
            source_type="telegram",
            media_path="/app/data/memes/test.jpg",
            mime_type=mime_type,
            width=800,
            height=600,
            language="en",
            category="dev",
            description_en="Test meme",
            is_site_worthy=True,
            telegram_message_id=None,
        )
        db.add(meme)
        db.commit()
        db.refresh(meme)
        return "Meme saved (pending review)."

    mock_process.side_effect = _fake_process

    resp = admin_client.post(
        "/api/v1/admin/memes/upload",
        files={"file": ("meme.jpg", b"fake-image-data", "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_type"] == "upload"
    assert data["mime_type"] == "image/jpeg"
    assert data["status"] == "pending"
    mock_process.assert_called_once()


@patch("src.admin.memes.process_meme")
def test_upload_meme_with_source_url(
    mock_process: MagicMock, admin_client: TestClient, db_session: Session
) -> None:
    """Upload with source_url passes it as caption in message dict."""

    def _fake_process(
        file_data: bytes,
        mime_type: str,
        message: dict[str, object],
        db: Session,
        **kwargs: object,
    ) -> str:
        # Verify caption was set from source_url
        assert message.get("caption") == "https://example.com/meme.jpg"
        meme = Meme(
            status="pending",
            source_type="telegram",
            source_url="https://example.com/meme.jpg",
            media_path="/app/data/memes/test.jpg",
            mime_type=mime_type,
        )
        db.add(meme)
        db.commit()
        return "Meme saved."

    mock_process.side_effect = _fake_process

    resp = admin_client.post(
        "/api/v1/admin/memes/upload",
        files={"file": ("meme.jpg", b"fake-image-data", "image/jpeg")},
        data={"source_url": "https://example.com/meme.jpg"},
    )
    assert resp.status_code == 200
