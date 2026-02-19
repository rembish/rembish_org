"""Tests for travel documents, vault file attachments, and trip associations."""

import base64
import tempfile
from collections.abc import Generator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.session import get_vault_user
from src.database import Base, get_db
from src.main import app
from src.models import User, VaultDocument, VaultVaccination
from src.vault_storage import LocalVaultStorage

# Test encryption key: 32 zero bytes, base64-encoded
TEST_KEY = base64.b64encode(b"\x00" * 32).decode()


@pytest.fixture(autouse=True)
def _set_vault_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.config.settings.vault_encryption_key", TEST_KEY)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    user = User(
        email="admin@test.com",
        name="Test Admin",
        nickname="admin",
        is_admin=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def vault_client(db_session: Session, admin_user: User) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_vault_user() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_vault_user] = override_get_vault_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def tmp_storage() -> Generator[LocalVaultStorage, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield LocalVaultStorage(Path(tmpdir))


# --- Storage tests ---


def test_local_storage_roundtrip(tmp_storage: LocalVaultStorage) -> None:
    key = tmp_storage.save(1, "test.pdf", b"hello world", "application/pdf")
    assert tmp_storage.exists(key)
    assert tmp_storage.read(key) == b"hello world"
    assert tmp_storage.delete(key) is True
    assert not tmp_storage.exists(key)


def test_generate_key_format(tmp_storage: LocalVaultStorage) -> None:
    key = tmp_storage.generate_key(42, "document.pdf")
    parts = key.split("/")
    assert parts[0] == "42"
    assert parts[1].endswith(".pdf")
    assert len(parts[1]) == 36  # 32 hex chars + ".pdf"


def test_delete_nonexistent(tmp_storage: LocalVaultStorage) -> None:
    assert tmp_storage.delete("nonexistent/file.pdf") is False


def test_read_nonexistent(tmp_storage: LocalVaultStorage) -> None:
    assert tmp_storage.read("nonexistent/file.pdf") is None


# --- Travel document CRUD tests ---


def test_create_travel_doc(vault_client: TestClient, admin_user: User) -> None:
    res = vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={
            "user_id": admin_user.id,
            "doc_type": "e_visa",
            "label": "India e-Visa",
            "country_code": "IN",
            "valid_from": "2026-01-01",
            "valid_until": "2026-12-31",
            "entry_type": "multiple",
            "notes": "Application ID: 12345",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["label"] == "India e-Visa"
    assert data["doc_type"] == "e_visa"
    assert data["country_code"] == "IN"
    assert data["entry_type"] == "multiple"
    assert data["notes_masked"] is not None
    assert data["notes_decrypted"] == "Application ID: 12345"
    assert data["id"] > 0
    assert data["files"] == []
    assert data["trip_ids"] == []


def test_list_travel_docs(vault_client: TestClient, admin_user: User) -> None:
    for label in ("Doc A", "Doc B"):
        vault_client.post(
            "/api/v1/admin/vault/travel-docs",
            json={
                "user_id": admin_user.id,
                "doc_type": "eta",
                "label": label,
            },
        )
    res = vault_client.get("/api/v1/admin/vault/travel-docs")
    assert res.status_code == 200
    docs = res.json()["travel_docs"]
    assert len(docs) == 2


def test_list_travel_docs_filter_by_user(
    vault_client: TestClient, admin_user: User, db_session: Session
) -> None:
    other = User(email="other@test.com", name="Other", is_admin=False, is_active=True)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={"user_id": admin_user.id, "doc_type": "esta", "label": "Admin doc"},
    )
    vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={"user_id": other.id, "doc_type": "esta", "label": "Other doc"},
    )

    res = vault_client.get("/api/v1/admin/vault/travel-docs", params={"user_id": other.id})
    docs = res.json()["travel_docs"]
    assert len(docs) == 1
    assert docs[0]["label"] == "Other doc"


def test_update_travel_doc(vault_client: TestClient, admin_user: User) -> None:
    create_res = vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={
            "user_id": admin_user.id,
            "doc_type": "e_visa",
            "label": "Old Label",
            "notes": "old notes",
        },
    )
    doc_id = create_res.json()["id"]

    update_res = vault_client.put(
        f"/api/v1/admin/vault/travel-docs/{doc_id}",
        json={
            "user_id": admin_user.id,
            "doc_type": "eta",
            "label": "New Label",
            "notes": "new notes",
        },
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["label"] == "New Label"
    assert data["doc_type"] == "eta"
    assert data["notes_decrypted"] == "new notes"


@patch("src.vault_storage.get_vault_storage")
def test_delete_travel_doc(
    mock_storage_fn: MagicMock,
    vault_client: TestClient,
    admin_user: User,
) -> None:
    mock_storage = MagicMock()
    mock_storage.delete.return_value = True
    mock_storage_fn.return_value = mock_storage

    create_res = vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={"user_id": admin_user.id, "doc_type": "loi", "label": "To Delete"},
    )
    doc_id = create_res.json()["id"]

    res = vault_client.delete(f"/api/v1/admin/vault/travel-docs/{doc_id}")
    assert res.status_code == 204

    list_res = vault_client.get("/api/v1/admin/vault/travel-docs")
    assert len(list_res.json()["travel_docs"]) == 0


def test_travel_doc_not_found(vault_client: TestClient) -> None:
    res = vault_client.get("/api/v1/admin/vault/travel-docs")
    assert res.status_code == 200  # list returns empty

    res = vault_client.put(
        "/api/v1/admin/vault/travel-docs/999",
        json={"user_id": 1, "doc_type": "other", "label": "x"},
    )
    assert res.status_code == 404

    res = vault_client.delete("/api/v1/admin/vault/travel-docs/999")
    assert res.status_code == 404


# --- File attachment tests ---


@patch("src.vault_storage.get_vault_storage")
def test_upload_file_to_document(
    mock_storage_fn: MagicMock,
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    # Create a document first
    doc = VaultDocument(
        user_id=admin_user.id, doc_type="passport", label="Test Passport"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    mock_storage = MagicMock()
    mock_storage.save.return_value = f"{admin_user.id}/abc123.pdf"
    mock_storage_fn.return_value = mock_storage

    res = vault_client.post(
        "/api/v1/admin/vault/files/upload",
        data={"entity_type": "document", "entity_id": str(doc.id)},
        files={"file": ("scan.pdf", b"%PDF-content", "application/pdf")},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] == 12
    assert data["sort_order"] == 0


@patch("src.vault_storage.get_vault_storage")
def test_upload_file_to_vaccination(
    mock_storage_fn: MagicMock,
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    vax = VaultVaccination(
        user_id=admin_user.id, vaccine_name="Yellow Fever"
    )
    db_session.add(vax)
    db_session.commit()
    db_session.refresh(vax)

    mock_storage = MagicMock()
    mock_storage.save.return_value = f"{admin_user.id}/def456.jpg"
    mock_storage_fn.return_value = mock_storage

    res = vault_client.post(
        "/api/v1/admin/vault/files/upload",
        data={"entity_type": "vaccination", "entity_id": str(vax.id)},
        files={"file": ("page.jpg", b"\xff\xd8\xff", "image/jpeg")},
    )
    assert res.status_code == 201
    assert res.json()["mime_type"] == "image/jpeg"


@patch("src.vault_storage.get_vault_storage")
def test_delete_file(
    mock_storage_fn: MagicMock,
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    from src.models.vault import VaultFile, VaultTravelDoc

    td = VaultTravelDoc(
        user_id=admin_user.id, doc_type="e_visa", label="Test"
    )
    db_session.add(td)
    db_session.flush()
    vf = VaultFile(
        travel_doc_id=td.id,
        file_path=f"{admin_user.id}/test.pdf",
        mime_type="application/pdf",
        file_size=100,
        sort_order=0,
    )
    db_session.add(vf)
    db_session.commit()
    db_session.refresh(vf)

    mock_storage = MagicMock()
    mock_storage.delete.return_value = True
    mock_storage_fn.return_value = mock_storage

    res = vault_client.delete(f"/api/v1/admin/vault/files/{vf.id}")
    assert res.status_code == 204
    mock_storage.delete.assert_called_once()


@patch("src.vault_storage.get_vault_storage")
def test_multiple_files_sort_order(
    mock_storage_fn: MagicMock,
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    doc = VaultDocument(
        user_id=admin_user.id, doc_type="passport", label="Multi-file"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    mock_storage = MagicMock()
    mock_storage.save.return_value = "key.pdf"
    mock_storage_fn.return_value = mock_storage

    # Upload first file
    res1 = vault_client.post(
        "/api/v1/admin/vault/files/upload",
        data={"entity_type": "document", "entity_id": str(doc.id), "label": "Front"},
        files={"file": ("front.jpg", b"\xff\xd8\xff", "image/jpeg")},
    )
    assert res1.json()["sort_order"] == 0

    # Upload second file
    res2 = vault_client.post(
        "/api/v1/admin/vault/files/upload",
        data={"entity_type": "document", "entity_id": str(doc.id), "label": "Back"},
        files={"file": ("back.jpg", b"\xff\xd8\xff", "image/jpeg")},
    )
    assert res2.json()["sort_order"] == 1


@patch("src.vault_storage.get_vault_storage")
def test_get_file_signed_url(
    mock_storage_fn: MagicMock,
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    from src.models.vault import VaultFile, VaultTravelDoc

    td = VaultTravelDoc(user_id=admin_user.id, doc_type="eta", label="URL Test")
    db_session.add(td)
    db_session.flush()
    vf = VaultFile(
        travel_doc_id=td.id,
        file_path="1/abc.pdf",
        mime_type="application/pdf",
        file_size=50,
        sort_order=0,
    )
    db_session.add(vf)
    db_session.commit()
    db_session.refresh(vf)

    mock_storage = MagicMock()
    mock_storage.get_signed_url.return_value = "/vault-files/1/abc.pdf"
    mock_storage_fn.return_value = mock_storage

    res = vault_client.get(f"/api/v1/admin/vault/files/{vf.id}/url")
    assert res.status_code == 200
    assert res.json()["url"] == "/vault-files/1/abc.pdf"


def test_file_not_found(vault_client: TestClient) -> None:
    res = vault_client.get("/api/v1/admin/vault/files/999/url")
    assert res.status_code == 404

    res = vault_client.delete("/api/v1/admin/vault/files/999")
    assert res.status_code == 404


# --- AI extraction tests ---


def test_extraction_disabled_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.config.settings.anthropic_api_key", "")
    from src.extraction import extract_document_metadata

    result = extract_document_metadata(b"%PDF-1.4 content", "application/pdf")
    assert result.metadata is None
    assert result.error == "API key not configured"


@patch("anthropic.Anthropic")
def test_extraction_returns_parsed_metadata(
    mock_anthropic_cls: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.config.settings.anthropic_api_key", "test-key")
    from src.extraction import extract_document_metadata

    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text='{"doc_type": "e_visa", "label": "India e-Visa", "country_code": "IN", '
            '"valid_from": "2026-01-01", "valid_until": "2026-12-31", '
            '"entry_type": "multiple", "notes": "Ref: ABC123"}'
        )
    ]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_cls.return_value = mock_client

    result = extract_document_metadata(b"%PDF-content", "application/pdf")
    assert result.error is None
    assert result.metadata is not None
    assert result.metadata.doc_type == "e_visa"
    assert result.metadata.label == "India e-Visa"
    assert result.metadata.country_code == "IN"
    assert result.metadata.entry_type == "multiple"


@patch("anthropic.Anthropic")
def test_extraction_invalid_json(
    mock_anthropic_cls: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.config.settings.anthropic_api_key", "test-key")
    from src.extraction import extract_document_metadata

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="this is not json")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_cls.return_value = mock_client

    result = extract_document_metadata(b"%PDF-content", "application/pdf")
    assert result.metadata is None
    assert result.error == "Failed to parse AI response"


# --- Trip association tests ---


def test_assign_doc_to_trip(
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    from src.models.travel import Trip

    # Create trip
    trip = Trip(start_date=date(2026, 6, 1), end_date=date(2026, 6, 15))
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Create travel doc
    create_res = vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={
            "user_id": admin_user.id,
            "doc_type": "e_visa",
            "label": "Trip Doc",
            "country_code": "IN",
        },
    )
    doc_id = create_res.json()["id"]

    # Assign
    res = vault_client.post(f"/api/v1/admin/vault/travel-docs/{doc_id}/trips/{trip.id}")
    assert res.status_code == 201

    # Verify trip_ids in list
    list_res = vault_client.get("/api/v1/admin/vault/travel-docs")
    docs = list_res.json()["travel_docs"]
    assert trip.id in docs[0]["trip_ids"]


def test_assign_doc_to_trip_idempotent(
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    from src.models.travel import Trip

    trip = Trip(start_date=date(2026, 7, 1))
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    create_res = vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={"user_id": admin_user.id, "doc_type": "eta", "label": "Dup"},
    )
    doc_id = create_res.json()["id"]

    # Assign twice
    vault_client.post(f"/api/v1/admin/vault/travel-docs/{doc_id}/trips/{trip.id}")
    res = vault_client.post(f"/api/v1/admin/vault/travel-docs/{doc_id}/trips/{trip.id}")
    assert res.status_code == 201
    assert res.json()["message"] == "Already assigned"


def test_unassign_doc_from_trip(
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    from src.models.travel import Trip

    trip = Trip(start_date=date(2026, 8, 1))
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    create_res = vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={"user_id": admin_user.id, "doc_type": "esta", "label": "Unassign"},
    )
    doc_id = create_res.json()["id"]

    vault_client.post(f"/api/v1/admin/vault/travel-docs/{doc_id}/trips/{trip.id}")
    res = vault_client.delete(f"/api/v1/admin/vault/travel-docs/{doc_id}/trips/{trip.id}")
    assert res.status_code == 204

    # Verify unassigned
    list_res = vault_client.get("/api/v1/admin/vault/travel-docs")
    docs = list_res.json()["travel_docs"]
    assert docs[0]["trip_ids"] == []


def test_suggest_travel_docs(
    vault_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    from src.models.travel import Trip

    trip = Trip(start_date=date(2026, 9, 1), end_date=date(2026, 9, 15))
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Create valid doc
    vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={
            "user_id": admin_user.id,
            "doc_type": "e_visa",
            "label": "Valid IN",
            "country_code": "IN",
            "valid_until": "2027-01-01",
        },
    )
    # Create expired doc
    vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={
            "user_id": admin_user.id,
            "doc_type": "e_visa",
            "label": "Expired IN",
            "country_code": "IN",
            "valid_until": "2020-01-01",
        },
    )
    # Create doc for different country
    vault_client.post(
        "/api/v1/admin/vault/travel-docs",
        json={
            "user_id": admin_user.id,
            "doc_type": "eta",
            "label": "UK ETA",
            "country_code": "GB",
        },
    )

    # Suggest for IN
    res = vault_client.get(
        "/api/v1/admin/vault/travel-docs/suggest",
        params={"country_code": "IN"},
    )
    assert res.status_code == 200
    docs = res.json()["travel_docs"]
    assert len(docs) == 1
    assert docs[0]["label"] == "Valid IN"

    # Assign the valid one and suggest again — should return empty
    doc_id = docs[0]["id"]
    vault_client.post(f"/api/v1/admin/vault/travel-docs/{doc_id}/trips/{trip.id}")
    res = vault_client.get(
        "/api/v1/admin/vault/travel-docs/suggest",
        params={"country_code": "IN", "trip_id": trip.id},
    )
    assert len(res.json()["travel_docs"]) == 0
