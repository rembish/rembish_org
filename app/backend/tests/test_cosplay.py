"""Tests for cosplay gallery endpoints (admin + public)."""

import io
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from src.models import CosplayCostume, CosplayPhoto


def _make_jpeg(width: int = 100, height: int = 150) -> io.BytesIO:
    buf = io.BytesIO()
    Image.new("RGB", (width, height)).save(buf, "JPEG")
    buf.seek(0)
    return buf


def _mock_storage() -> MagicMock:
    storage = MagicMock()
    storage.save.return_value = "/app/data/cosplay/fake.jpg"
    return storage


# --- Admin CRUD ---


def test_list_costumes_empty(admin_client: TestClient) -> None:
    res = admin_client.get("/api/v1/admin/cosplay")
    assert res.status_code == 200
    assert res.json() == []


def test_create_costume(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/admin/cosplay",
        json={"name": "Plague Doctor", "description": "Dark vibes", "sort_order": 0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Plague Doctor"
    assert data["description"] == "Dark vibes"
    assert data["photos"] == []


def test_update_costume(admin_client: TestClient) -> None:
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "Old Name"})
    costume_id = res.json()["id"]
    res = admin_client.put(
        f"/api/v1/admin/cosplay/{costume_id}",
        json={"name": "New Name", "sort_order": 1},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"


def test_update_costume_not_found(admin_client: TestClient) -> None:
    res = admin_client.put("/api/v1/admin/cosplay/999", json={"name": "X"})
    assert res.status_code == 404


def test_delete_costume(admin_client: TestClient, db_session: Session) -> None:
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "To Delete"})
    costume_id = res.json()["id"]
    res = admin_client.delete(f"/api/v1/admin/cosplay/{costume_id}")
    assert res.status_code == 204
    assert db_session.query(CosplayCostume).filter_by(id=costume_id).first() is None


def test_delete_costume_not_found(admin_client: TestClient) -> None:
    res = admin_client.delete("/api/v1/admin/cosplay/999")
    assert res.status_code == 404


# --- Photo upload ---


@patch("src.admin.cosplay.get_storage")
def test_upload_photo(
    mock_get_storage: MagicMock, admin_client: TestClient, db_session: Session
) -> None:
    mock_get_storage.return_value = _mock_storage()
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "Test Costume"})
    costume_id = res.json()["id"]

    res = admin_client.post(
        f"/api/v1/admin/cosplay/{costume_id}/photos",
        files={"file": ("test.jpg", _make_jpeg(100, 150), "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["width"] == 100
    assert data["height"] == 150
    assert data["sort_order"] == 0

    photo = db_session.query(CosplayPhoto).filter_by(costume_id=costume_id).first()
    assert photo is not None
    assert photo.filename.endswith(".jpg")


def test_upload_photo_invalid_type(admin_client: TestClient) -> None:
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "C"})
    costume_id = res.json()["id"]
    res = admin_client.post(
        f"/api/v1/admin/cosplay/{costume_id}/photos",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 400


def test_upload_photo_empty(admin_client: TestClient) -> None:
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "C"})
    costume_id = res.json()["id"]
    res = admin_client.post(
        f"/api/v1/admin/cosplay/{costume_id}/photos",
        files={"file": ("test.jpg", b"", "image/jpeg")},
    )
    assert res.status_code == 400


def test_upload_photo_costume_not_found(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/admin/cosplay/999/photos",
        files={"file": ("test.jpg", _make_jpeg(), "image/jpeg")},
    )
    assert res.status_code == 404


# --- Photo delete + reorder ---


@patch("src.admin.cosplay.get_storage")
def test_delete_photo(
    mock_get_storage: MagicMock, admin_client: TestClient, db_session: Session
) -> None:
    mock_get_storage.return_value = _mock_storage()
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "C"})
    costume_id = res.json()["id"]

    res = admin_client.post(
        f"/api/v1/admin/cosplay/{costume_id}/photos",
        files={"file": ("p.jpg", _make_jpeg(50, 50), "image/jpeg")},
    )
    photo_id = res.json()["id"]

    res = admin_client.delete(f"/api/v1/admin/cosplay/{costume_id}/photos/{photo_id}")
    assert res.status_code == 204
    assert db_session.query(CosplayPhoto).filter_by(id=photo_id).first() is None


def test_delete_photo_not_found(admin_client: TestClient) -> None:
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "C"})
    costume_id = res.json()["id"]
    res = admin_client.delete(f"/api/v1/admin/cosplay/{costume_id}/photos/999")
    assert res.status_code == 404


@patch("src.admin.cosplay.get_storage")
def test_reorder_photos(
    mock_get_storage: MagicMock, admin_client: TestClient, db_session: Session
) -> None:
    mock_get_storage.return_value = _mock_storage()
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "C"})
    costume_id = res.json()["id"]

    ids = []
    for _ in range(3):
        res = admin_client.post(
            f"/api/v1/admin/cosplay/{costume_id}/photos",
            files={"file": ("p.jpg", _make_jpeg(10, 10), "image/jpeg")},
        )
        ids.append(res.json()["id"])

    res = admin_client.put(
        f"/api/v1/admin/cosplay/{costume_id}/photos/reorder",
        json={"photo_ids": list(reversed(ids))},
    )
    assert res.status_code == 200

    photos = (
        db_session.query(CosplayPhoto)
        .filter_by(costume_id=costume_id)
        .order_by(CosplayPhoto.sort_order)
        .all()
    )
    assert [p.id for p in photos] == list(reversed(ids))


@patch("src.admin.cosplay.get_storage")
def test_set_cover_photo(
    mock_get_storage: MagicMock, admin_client: TestClient, db_session: Session
) -> None:
    mock_get_storage.return_value = _mock_storage()
    res = admin_client.post("/api/v1/admin/cosplay", json={"name": "C"})
    costume_id = res.json()["id"]
    assert res.json()["cover_photo_id"] is None

    res = admin_client.post(
        f"/api/v1/admin/cosplay/{costume_id}/photos",
        files={"file": ("p.jpg", _make_jpeg(10, 10), "image/jpeg")},
    )
    photo_id = res.json()["id"]

    res = admin_client.put(f"/api/v1/admin/cosplay/{costume_id}/cover/{photo_id}")
    assert res.status_code == 200

    res = admin_client.get("/api/v1/admin/cosplay")
    assert res.json()[0]["cover_photo_id"] == photo_id


def test_reorder_photos_costume_not_found(admin_client: TestClient) -> None:
    res = admin_client.put(
        "/api/v1/admin/cosplay/999/photos/reorder",
        json={"photo_ids": [1, 2]},
    )
    assert res.status_code == 404


# --- Public endpoints ---


def test_public_list_costumes(client: TestClient, db_session: Session) -> None:
    c = CosplayCostume(name="Public Test", sort_order=0)
    db_session.add(c)
    db_session.flush()
    p = CosplayPhoto(costume_id=c.id, filename="test.jpg", width=100, height=200, sort_order=0)
    db_session.add(p)
    db_session.commit()

    res = client.get("/api/v1/travels/cosplay")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "Public Test"
    assert len(data[0]["photos"]) == 1


def test_public_photo_not_found(client: TestClient) -> None:
    res = client.get("/api/v1/travels/cosplay/photos/999")
    assert res.status_code == 404
