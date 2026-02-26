"""Tests for trip document management (upload, update, delete, download, documents-tab)."""

from collections.abc import Generator
from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.auth.session import get_admin_user, get_trips_viewer, get_vault_user
from src.database import get_db
from src.main import app
from src.models import Trip, TripDocument, User


def _create_trip(db: Session, *, start: date | None = None, end: date | None = None) -> Trip:
    trip = Trip(
        start_date=start or date(2026, 6, 1),
        end_date=end or date(2026, 6, 15),
        trip_type="regular",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def _create_doc(
    db: Session,
    trip: Trip,
    *,
    label: str = "Insurance",
    path: str = "1/abc.pdf",
    name: str = "insurance.pdf",
    mime: str = "application/pdf",
    size: int = 1024,
    notes: str | None = None,
    sort_order: int = 0,
) -> TripDocument:
    doc = TripDocument(
        trip_id=trip.id,
        label=label,
        document_path=path,
        document_name=name,
        document_mime_type=mime,
        document_size=size,
        notes=notes,
        sort_order=sort_order,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# --- Fixtures ---


def _make_admin_client(
    db_session: Session, admin_user: User
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_admin_user() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_admin_user] = override_get_admin_user
    app.dependency_overrides[get_trips_viewer] = override_get_admin_user
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


def _make_vault_client(
    db_session: Session, admin_user: User
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_admin_user() -> User:
        return admin_user

    def override_get_vault_user() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_admin_user] = override_get_admin_user
    app.dependency_overrides[get_trips_viewer] = override_get_admin_user
    app.dependency_overrides[get_vault_user] = override_get_vault_user
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


# --- Documents tab endpoint ---


def test_documents_tab_empty_trip(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    with patch(
        "src.travels.trip_documents.get_trip_travel_docs", return_value={}
    ), patch("src.travels.trip_documents.get_trip_vaccination_needs", return_value=[]):
        res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/documents-tab")
    assert res.status_code == 200
    data = res.json()
    assert data["passports"] == []
    assert data["travel_docs"] == []
    assert data["required_vaccines"] == []
    assert data["documents"] == []


def test_documents_tab_with_trip_documents(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)
    _create_doc(db_session, trip, label="Voucher", sort_order=0)
    _create_doc(db_session, trip, label="Receipt", sort_order=1)

    with patch(
        "src.travels.trip_documents.get_trip_travel_docs", return_value={}
    ), patch("src.travels.trip_documents.get_trip_vaccination_needs", return_value=[]):
        res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/documents-tab")
    assert res.status_code == 200
    data = res.json()
    assert len(data["documents"]) == 2
    assert data["documents"][0]["label"] == "Voucher"
    assert data["documents"][1]["label"] == "Receipt"


def test_documents_tab_trip_not_found(admin_client: TestClient) -> None:
    res = admin_client.get("/api/v1/travels/trips/9999/documents-tab")
    assert res.status_code == 404


# --- Upload endpoint ---


@patch("src.vault_storage.get_vault_storage")
def test_upload_document(
    mock_storage_fn: MagicMock,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    mock_storage = MagicMock()
    mock_storage.save.return_value = "1/uploaded.pdf"
    mock_storage_fn.return_value = mock_storage

    trip = _create_trip(db_session)
    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/documents",
        data={"label": "Travel Insurance", "notes": "Policy #123"},
        files={"file": ("policy.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["label"] == "Travel Insurance"
    assert data["document_name"] == "policy.pdf"
    assert data["document_mime_type"] == "application/pdf"
    assert data["notes"] == "Policy #123"
    assert data["sort_order"] == 0

    mock_storage.save.assert_called_once()


@patch("src.vault_storage.get_vault_storage")
def test_upload_document_sort_order_increments(
    mock_storage_fn: MagicMock,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    mock_storage = MagicMock()
    mock_storage.save.return_value = "1/doc.pdf"
    mock_storage_fn.return_value = mock_storage

    trip = _create_trip(db_session)
    _create_doc(db_session, trip, sort_order=2)

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/documents",
        data={"label": "Second Doc"},
        files={"file": ("doc.pdf", b"content", "application/pdf")},
    )
    assert res.status_code == 200
    assert res.json()["sort_order"] == 3


@patch("src.vault_storage.get_vault_storage")
def test_upload_document_without_notes(
    mock_storage_fn: MagicMock,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    mock_storage = MagicMock()
    mock_storage.save.return_value = "1/doc.pdf"
    mock_storage_fn.return_value = mock_storage

    trip = _create_trip(db_session)
    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/documents",
        data={"label": "Boarding Pass"},
        files={"file": ("pass.pdf", b"content", "application/pdf")},
    )
    assert res.status_code == 200
    assert res.json()["notes"] is None


def test_upload_unsupported_mime_type(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)
    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/documents",
        data={"label": "Doc"},
        files={"file": ("doc.txt", b"text content", "text/plain")},
    )
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]


@patch("src.vault_storage.get_vault_storage")
def test_upload_file_too_large(
    mock_storage_fn: MagicMock,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    trip = _create_trip(db_session)
    big_content = b"x" * (10 * 1024 * 1024 + 1)
    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/documents",
        data={"label": "Big File"},
        files={"file": ("big.pdf", big_content, "application/pdf")},
    )
    assert res.status_code == 400
    assert "too large" in res.json()["detail"]


def test_upload_trip_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/trips/9999/documents",
        data={"label": "Doc"},
        files={"file": ("doc.pdf", b"content", "application/pdf")},
    )
    assert res.status_code == 404


def test_upload_requires_auth(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    res = client.post(
        f"/api/v1/travels/trips/{trip.id}/documents",
        data={"label": "Doc"},
        files={"file": ("doc.pdf", b"content", "application/pdf")},
    )
    assert res.status_code == 401


# --- Update endpoint ---


def test_update_document(admin_client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip, label="Old Label", notes="Old notes")

    res = admin_client.put(
        f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}",
        data={"label": "New Label", "notes": "New notes"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["label"] == "New Label"
    assert data["notes"] == "New notes"


def test_update_document_clear_notes(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip, label="Doc", notes="Some notes")

    res = admin_client.put(
        f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}",
        data={"label": "Updated"},
    )
    assert res.status_code == 200
    assert res.json()["notes"] is None


def test_update_document_not_found(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)
    res = admin_client.put(
        f"/api/v1/travels/trips/{trip.id}/documents/999",
        data={"label": "X"},
    )
    assert res.status_code == 404


def test_update_requires_auth(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip)
    res = client.put(
        f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}",
        data={"label": "X"},
    )
    assert res.status_code == 401


# --- Delete endpoint ---


@patch("src.vault_storage.get_vault_storage")
def test_delete_document(
    mock_storage_fn: MagicMock,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    mock_storage = MagicMock()
    mock_storage_fn.return_value = mock_storage

    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip, path="1/to-delete.pdf")

    res = admin_client.delete(f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}")
    assert res.status_code == 204

    mock_storage.delete.assert_called_once_with("1/to-delete.pdf")

    remaining = db_session.query(TripDocument).filter(TripDocument.id == doc.id).first()
    assert remaining is None


@patch("src.vault_storage.get_vault_storage")
def test_delete_document_storage_failure_still_deletes_record(
    mock_storage_fn: MagicMock,
    admin_client: TestClient,
    db_session: Session,
) -> None:
    mock_storage = MagicMock()
    mock_storage.delete.side_effect = Exception("Storage error")
    mock_storage_fn.return_value = mock_storage

    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip)

    res = admin_client.delete(f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}")
    assert res.status_code == 204

    remaining = db_session.query(TripDocument).filter(TripDocument.id == doc.id).first()
    assert remaining is None


def test_delete_document_not_found(
    admin_client: TestClient, db_session: Session
) -> None:
    trip = _create_trip(db_session)
    res = admin_client.delete(f"/api/v1/travels/trips/{trip.id}/documents/999")
    assert res.status_code == 404


def test_delete_requires_auth(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip)
    res = client.delete(f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}")
    assert res.status_code == 401


# --- File download endpoint ---


@patch("src.vault_storage.get_vault_storage")
def test_download_file(
    mock_storage_fn: MagicMock,
    db_session: Session,
    admin_user: User,
) -> None:
    mock_storage = MagicMock()
    mock_storage.read.return_value = b"pdf-bytes-here"
    mock_storage_fn.return_value = mock_storage

    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip, path="1/file.pdf", mime="application/pdf")

    for c in _make_vault_client(db_session, admin_user):
        res = c.get(f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}/file")
    assert res.status_code == 200
    assert res.content == b"pdf-bytes-here"
    assert res.headers["content-type"] == "application/pdf"


@patch("src.vault_storage.get_vault_storage")
def test_download_file_not_in_storage(
    mock_storage_fn: MagicMock,
    db_session: Session,
    admin_user: User,
) -> None:
    mock_storage = MagicMock()
    mock_storage.read.return_value = None
    mock_storage_fn.return_value = mock_storage

    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip, path="1/missing.pdf")

    for c in _make_vault_client(db_session, admin_user):
        res = c.get(f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}/file")
    assert res.status_code == 404


def test_download_file_doc_not_found(
    db_session: Session,
    admin_user: User,
) -> None:
    trip = _create_trip(db_session)
    for c in _make_vault_client(db_session, admin_user):
        res = c.get(f"/api/v1/travels/trips/{trip.id}/documents/999/file")
    assert res.status_code == 404


def test_download_requires_vault_auth(client: TestClient, db_session: Session) -> None:
    trip = _create_trip(db_session)
    doc = _create_doc(db_session, trip)
    res = client.get(f"/api/v1/travels/trips/{trip.id}/documents/{doc.id}/file")
    assert res.status_code == 401
