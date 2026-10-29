"""Tests for the Instagram sync against a fake Graph API.

The fake serves numbered posts in pages, hands out a `paging.next` URL that fails the way
Meta's did ("(#200) Provide valid app ID"), and can start rate limiting after a number of
media lookups.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from src.admin import instagram as ig
from src.auth.session import get_admin_user
from src.database import get_db
from src.main import app
from src.models import InstagramPost, User

TOKEN = "SECRET-TEST-TOKEN"
ACCOUNT = "1000"


def _jpeg() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (4, 3)).save(buf, format="JPEG")
    return buf.getvalue()


class FakeGraph:
    def __init__(self, count: int, rate_limit_after: int | None = None) -> None:
        start = datetime(2030, 1, 1, tzinfo=UTC)
        self.posts = [
            {
                "id": f"9{i:04d}",
                "caption": f"Post {i}",
                "media_type": "IMAGE",
                "timestamp": (start - timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%S+0000"),
                "permalink": f"https://instagram.test/p/{i}",
            }
            for i in range(count)
        ]
        self.rate_limit_after = rate_limit_after
        self.media_calls = 0
        self.image = _jpeg()

    def _json(self, status: int, body: dict[str, Any], **headers: str) -> httpx.Response:
        return httpx.Response(status, json=body, headers=headers, request=httpx.Request("GET", "x"))

    def get(self, url: str, params: dict[str, Any] | None = None, **_: Any) -> httpx.Response:
        params = params or {}
        path = urlsplit(url).path
        if "broken-next" in url:
            error = {"message": "(#200) Provide valid app ID", "code": 200}
            return self._json(403, {"error": error})
        if url.startswith("https://cdn.test/"):
            return httpx.Response(200, content=self.image, request=httpx.Request("GET", url))
        assert params.get("access_token") == TOKEN
        if path.endswith(f"/{ACCOUNT}/media"):
            offset = int(params.get("after") or 0)
            limit = int(params["limit"])
            page = self.posts[offset : offset + limit]
            body: dict[str, Any] = {"data": page}
            if offset + limit < len(self.posts):
                body["paging"] = {
                    "cursors": {"after": str(offset + limit)},
                    "next": f"https://graph.test/broken-next?access_token={TOKEN}",
                }
            return self._json(200, body)
        self.media_calls += 1
        if self.rate_limit_after is not None and self.media_calls > self.rate_limit_after:
            usage = '{"1":[{"type":"instagram","estimated_time_to_regain_access":12}]}'
            error = {"message": "(#4) Application request limit reached", "code": 4}
            return self._json(403, {"error": error}, **{"x-business-use-case-usage": usage})
        media_id = path.rsplit("/", 1)[-1]
        return self._json(200, {"media_url": f"https://cdn.test/{media_id}.jpg"})


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save(self, filename: str, content: bytes, content_type: str = "image/jpeg") -> str:
        self.files[filename] = content
        return f"https://storage.test/{filename}"


@pytest.fixture()
def sync_client(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> Generator[TestClient, None, None]:
    admin = User(email="sync@test.com", name="Sync", nickname="sync", role="admin", is_active=True)
    db_session.add(admin)
    db_session.commit()
    monkeypatch.setattr(ig.settings, "instagram_account_id", ACCOUNT)
    monkeypatch.setattr(ig.settings, "instagram_page_token", TOKEN)
    monkeypatch.setattr(ig, "get_storage", lambda: FakeStorage())
    monkeypatch.setattr(ig, "CURSOR_FILE", tmp_path / "cursor")
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_admin_user] = lambda: admin
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


def _use(monkeypatch: pytest.MonkeyPatch, graph: FakeGraph) -> None:
    monkeypatch.setattr(ig.httpx, "get", graph.get)


def test_sync_pages_by_cursor_not_next_url(
    sync_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, FakeGraph(70))
    r = sync_client.post("/api/v1/admin/instagram/sync-new")
    assert r.status_code == 200, r.text
    assert r.json()["fetched"] == 70
    assert db_session.query(InstagramPost).count() == 70


def test_sync_keeps_progress_when_rate_limited(
    sync_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, FakeGraph(70, rate_limit_after=30))
    r = sync_client.post("/api/v1/admin/instagram/sync-new")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["fetched"] == 30
    assert "then stopped" in body["message"] and "about 12 min" in body["message"]
    assert TOKEN not in r.text
    assert db_session.query(InstagramPost).count() == 30

    # The next run picks up where this one stopped
    _use(monkeypatch, FakeGraph(70))
    r = sync_client.post("/api/v1/admin/instagram/sync-new")
    assert r.json()["fetched"] == 40
    assert db_session.query(InstagramPost).count() == 70


def test_sync_rate_limited_at_once(
    sync_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, FakeGraph(5, rate_limit_after=0))
    r = sync_client.post("/api/v1/admin/instagram/sync-new")
    assert r.status_code == 429
    assert "(#4) Application request limit reached" in r.json()["detail"]
    assert TOKEN not in r.text


def test_sync_refuses_to_overlap(sync_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, FakeGraph(5))
    assert ig._sync_lock.acquire(blocking=False)
    try:
        r = sync_client.post("/api/v1/admin/instagram/sync-new")
    finally:
        ig._sync_lock.release()
    assert r.status_code == 409


def test_fetch_older_resumes_from_cursor(
    sync_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, FakeGraph(150))
    r = sync_client.post("/api/v1/admin/instagram/fetch?count=120")
    assert r.status_code == 200, r.text
    assert r.json()["fetched"] == 120
    r = sync_client.post("/api/v1/admin/instagram/fetch?count=100")
    assert r.json()["fetched"] == 30
    assert db_session.query(InstagramPost).count() == 150


def test_fill_gaps_stream(
    sync_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, FakeGraph(60))
    r = sync_client.get("/api/v1/admin/instagram/fill-gaps")
    assert r.status_code == 200
    assert '"done": true' in r.text and '"fetched": 60' in r.text
    assert db_session.query(InstagramPost).count() == 60
