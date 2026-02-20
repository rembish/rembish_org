"""Tests for vault (encrypted documents & loyalty programs)."""

import base64
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.session import get_vault_user
from src.crypto import decrypt, encrypt, mask_value
from src.database import Base, get_db
from src.main import app
from src.models import User

# Test encryption key: 32 zero bytes, base64-encoded
TEST_KEY = base64.b64encode(b"\x00" * 32).decode()


@pytest.fixture(autouse=True)
def _set_vault_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set VAULT_ENCRYPTION_KEY for all vault tests."""
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
def other_user(db_session: Session) -> User:
    user = User(
        email="other@test.com",
        name="Other User",
        nickname="other",
        is_admin=False,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def vault_client(db_session: Session, admin_user: User) -> Generator[TestClient, None, None]:
    """Test client with database + vault auth overrides."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_vault_user() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_vault_user] = override_get_vault_user
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def no_vault_client(
    db_session: Session,
) -> Generator[TestClient, None, None]:
    """Test client with database but NO vault auth (locked)."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-CSRF": "1"}) as c:
        yield c
    app.dependency_overrides.clear()


# --- Crypto tests ---


def test_encrypt_decrypt_roundtrip() -> None:
    plaintext = "AB123456CD"
    encrypted = encrypt(plaintext)
    assert isinstance(encrypted, bytes)
    assert len(encrypted) > 12  # nonce + ciphertext + tag
    assert decrypt(encrypted) == plaintext


def test_encrypt_produces_different_ciphertexts() -> None:
    """Each encryption uses a random nonce → different output."""
    ct1 = encrypt("same")
    ct2 = encrypt("same")
    assert ct1 != ct2
    assert decrypt(ct1) == decrypt(ct2) == "same"


def test_mask_short_value() -> None:
    assert mask_value("AB") == "\u2022\u2022"
    assert mask_value("ABCD") == "\u2022\u2022\u2022\u2022"


def test_mask_normal_value() -> None:
    assert mask_value("AB123456CD") == "AB\u2022\u2022\u2022\u2022\u2022\u2022CD"


def test_mask_empty_string() -> None:
    assert mask_value("") == ""


# --- Document CRUD tests ---


def test_create_document(vault_client: TestClient, admin_user: User) -> None:
    res = vault_client.post(
        "/api/v1/admin/vault/documents",
        json={
            "user_id": admin_user.id,
            "doc_type": "passport",
            "label": "CZ Passport",
            "issuing_country": "CZ",
            "issue_date": "2020-01-15",
            "expiry_date": "2030-01-15",
            "number": "AB123456",
            "notes": "Main passport",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["label"] == "CZ Passport"
    assert data["number_masked"] == "AB\u2022\u2022\u2022\u202256"
    assert data["number_decrypted"] == "AB123456"
    assert data["notes_decrypted"] == "Main passport"
    assert data["id"] > 0


def test_list_documents(vault_client: TestClient, admin_user: User) -> None:
    # Create two documents
    for label in ("Doc A", "Doc B"):
        vault_client.post(
            "/api/v1/admin/vault/documents",
            json={
                "user_id": admin_user.id,
                "doc_type": "id_card",
                "label": label,
            },
        )

    res = vault_client.get("/api/v1/admin/vault/documents")
    assert res.status_code == 200
    docs = res.json()["documents"]
    assert len(docs) == 2


def test_list_documents_filter_by_user(
    vault_client: TestClient, admin_user: User, other_user: User
) -> None:
    vault_client.post(
        "/api/v1/admin/vault/documents",
        json={
            "user_id": admin_user.id,
            "doc_type": "passport",
            "label": "Admin doc",
        },
    )
    vault_client.post(
        "/api/v1/admin/vault/documents",
        json={
            "user_id": other_user.id,
            "doc_type": "passport",
            "label": "Other doc",
        },
    )

    res = vault_client.get("/api/v1/admin/vault/documents", params={"user_id": other_user.id})
    docs = res.json()["documents"]
    assert len(docs) == 1
    assert docs[0]["label"] == "Other doc"


def test_update_document(vault_client: TestClient, admin_user: User) -> None:
    create_res = vault_client.post(
        "/api/v1/admin/vault/documents",
        json={
            "user_id": admin_user.id,
            "doc_type": "passport",
            "label": "Old Label",
            "number": "OLD123",
        },
    )
    doc_id = create_res.json()["id"]

    update_res = vault_client.put(
        f"/api/v1/admin/vault/documents/{doc_id}",
        json={
            "user_id": admin_user.id,
            "doc_type": "passport",
            "label": "New Label",
            "number": "NEW456",
        },
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["label"] == "New Label"
    assert data["number_decrypted"] == "NEW456"


def test_delete_document(vault_client: TestClient, admin_user: User) -> None:
    create_res = vault_client.post(
        "/api/v1/admin/vault/documents",
        json={
            "user_id": admin_user.id,
            "doc_type": "passport",
            "label": "To Archive",
        },
    )
    doc_id = create_res.json()["id"]

    res = vault_client.delete(f"/api/v1/admin/vault/documents/{doc_id}")
    assert res.status_code == 204

    # Verify archived (still in list but is_archived=True)
    list_res = vault_client.get("/api/v1/admin/vault/documents")
    docs = list_res.json()["documents"]
    assert len(docs) == 1
    assert docs[0]["is_archived"] is True

    # Verify restore
    restore_res = vault_client.post(f"/api/v1/admin/vault/documents/{doc_id}/restore")
    assert restore_res.status_code == 200
    assert restore_res.json()["is_archived"] is False


def test_delete_document_not_found(vault_client: TestClient) -> None:
    res = vault_client.delete("/api/v1/admin/vault/documents/999")
    assert res.status_code == 404


# --- Loyalty Program CRUD tests ---


def test_create_program(vault_client: TestClient, admin_user: User) -> None:
    res = vault_client.post(
        "/api/v1/admin/vault/programs",
        json={
            "user_id": admin_user.id,
            "program_name": "Miles & More",
            "alliance": "star_alliance",
            "tier": "Gold",
            "membership_number": "1234567890",
            "notes": "Main account",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["program_name"] == "Miles & More"
    assert data["alliance"] == "star_alliance"
    assert data["tier"] == "Gold"
    assert data["membership_number_masked"] == "12\u2022\u2022\u2022\u2022\u2022\u202290"
    assert data["membership_number_decrypted"] == "1234567890"


def test_list_programs(vault_client: TestClient, admin_user: User) -> None:
    for name in ("Prog A", "Prog B"):
        vault_client.post(
            "/api/v1/admin/vault/programs",
            json={
                "user_id": admin_user.id,
                "program_name": name,
            },
        )

    res = vault_client.get("/api/v1/admin/vault/programs")
    assert res.status_code == 200
    progs = res.json()["programs"]
    assert len(progs) == 2


def test_update_program(vault_client: TestClient, admin_user: User) -> None:
    create_res = vault_client.post(
        "/api/v1/admin/vault/programs",
        json={
            "user_id": admin_user.id,
            "program_name": "Old Name",
            "membership_number": "OLD123",
        },
    )
    prog_id = create_res.json()["id"]

    update_res = vault_client.put(
        f"/api/v1/admin/vault/programs/{prog_id}",
        json={
            "user_id": admin_user.id,
            "program_name": "New Name",
            "membership_number": "NEW456",
        },
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["program_name"] == "New Name"
    assert data["membership_number_decrypted"] == "NEW456"


def test_delete_program(vault_client: TestClient, admin_user: User) -> None:
    create_res = vault_client.post(
        "/api/v1/admin/vault/programs",
        json={
            "user_id": admin_user.id,
            "program_name": "To Delete",
        },
    )
    prog_id = create_res.json()["id"]

    res = vault_client.delete(f"/api/v1/admin/vault/programs/{prog_id}")
    assert res.status_code == 204


def test_delete_program_not_found(vault_client: TestClient) -> None:
    res = vault_client.delete("/api/v1/admin/vault/programs/999")
    assert res.status_code == 404


# --- Auth guard tests ---


def test_no_auth_returns_401(no_vault_client: TestClient) -> None:
    """Without any auth, vault endpoints return 401."""
    res = no_vault_client.get("/api/v1/admin/vault/documents")
    assert res.status_code == 401


def test_admin_without_vault_cookie_returns_401(db_session: Session, admin_user: User) -> None:
    """Admin user without vault cookie gets vault_locked."""
    from src.auth.session import get_admin_user

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_admin_user() -> User:
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_admin_user] = override_get_admin_user
    try:
        with TestClient(app, headers={"X-CSRF": "1"}) as c:
            res = c.get("/api/v1/admin/vault/documents")
            assert res.status_code == 401
            assert res.json()["detail"] == "vault_locked"
    finally:
        app.dependency_overrides.clear()


# --- Address CRUD tests ---


def test_create_address(vault_client: TestClient) -> None:
    res = vault_client.post(
        "/api/v1/admin/vault/addresses",
        json={
            "name": "Jane Doe",
            "address": "123 Main St, Apt 4B, 10115 Berlin",
            "country_code": "de",
            "notes": "Ring twice",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Jane Doe"
    assert data["address"] == "123 Main St, Apt 4B, 10115 Berlin"
    assert data["country_code"] == "DE"  # uppercased
    assert data["notes_decrypted"] == "Ring twice"
    assert data["notes_masked"] is not None
    assert data["id"] > 0


def test_create_address_required_fields(vault_client: TestClient) -> None:
    """Missing required fields should return 422."""
    res = vault_client.post(
        "/api/v1/admin/vault/addresses",
        json={"name": "Incomplete"},
    )
    assert res.status_code == 422


def test_list_addresses_alphabetical(vault_client: TestClient) -> None:
    for name in ("Zara", "Alice", "Marta"):
        vault_client.post(
            "/api/v1/admin/vault/addresses",
            json={"name": name, "address": "Str 1, Prague"},
        )
    res = vault_client.get("/api/v1/admin/vault/addresses")
    assert res.status_code == 200
    names = [a["name"] for a in res.json()["addresses"]]
    assert names == ["Alice", "Marta", "Zara"]


def test_search_addresses(vault_client: TestClient) -> None:
    vault_client.post(
        "/api/v1/admin/vault/addresses",
        json={"name": "Alice Wonder", "address": "Str 1, London"},
    )
    vault_client.post(
        "/api/v1/admin/vault/addresses",
        json={"name": "Bob Builder", "address": "Str 2, London"},
    )
    res = vault_client.get("/api/v1/admin/vault/addresses", params={"search": "alice"})
    addrs = res.json()["addresses"]
    assert len(addrs) == 1
    assert addrs[0]["name"] == "Alice Wonder"


def test_search_addresses_by_address(vault_client: TestClient) -> None:
    vault_client.post(
        "/api/v1/admin/vault/addresses",
        json={"name": "Alice", "address": "123 Baker Street, London"},
    )
    vault_client.post(
        "/api/v1/admin/vault/addresses",
        json={"name": "Bob", "address": "456 Oxford Road, Manchester"},
    )
    res = vault_client.get("/api/v1/admin/vault/addresses", params={"search": "baker"})
    addrs = res.json()["addresses"]
    assert len(addrs) == 1
    assert addrs[0]["name"] == "Alice"


def test_update_address(vault_client: TestClient) -> None:
    create_res = vault_client.post(
        "/api/v1/admin/vault/addresses",
        json={
            "name": "Old Name",
            "address": "Old St, Old City",
            "notes": "old note",
        },
    )
    addr_id = create_res.json()["id"]

    update_res = vault_client.put(
        f"/api/v1/admin/vault/addresses/{addr_id}",
        json={
            "name": "New Name",
            "address": "New St, New City",
        },
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "New Name"
    assert data["address"] == "New St, New City"
    assert data["notes_decrypted"] is None  # notes cleared


def test_delete_address(vault_client: TestClient) -> None:
    create_res = vault_client.post(
        "/api/v1/admin/vault/addresses",
        json={"name": "To Delete", "address": "Str 1, Wien"},
    )
    addr_id = create_res.json()["id"]

    res = vault_client.delete(f"/api/v1/admin/vault/addresses/{addr_id}")
    assert res.status_code == 204

    list_res = vault_client.get("/api/v1/admin/vault/addresses")
    assert len(list_res.json()["addresses"]) == 0


def test_delete_address_not_found(vault_client: TestClient) -> None:
    res = vault_client.delete("/api/v1/admin/vault/addresses/999")
    assert res.status_code == 404


def test_update_address_not_found(vault_client: TestClient) -> None:
    res = vault_client.put(
        "/api/v1/admin/vault/addresses/999",
        json={"name": "X", "address": "Y, Z"},
    )
    assert res.status_code == 404


def test_address_vault_auth_guard(no_vault_client: TestClient) -> None:
    """Addresses require vault auth."""
    res = no_vault_client.get("/api/v1/admin/vault/addresses")
    assert res.status_code == 401


def test_vault_status_unlocked(vault_client: TestClient) -> None:
    """Status endpoint works (though it checks cookie, not dependency override)."""
    # With the vault client, status check goes through regular auth path
    # Just verify the endpoint exists and returns a response
    res = vault_client.get("/api/auth/vault/status")
    assert res.status_code == 200
    data = res.json()
    assert "unlocked" in data
