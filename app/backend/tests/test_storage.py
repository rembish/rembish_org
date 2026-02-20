"""Tests for storage backends (LocalStorage + LocalVaultStorage)."""

import tempfile
from pathlib import Path

from src.storage import LocalStorage
from src.vault_storage import LocalVaultStorage


# --- LocalStorage (Instagram) ---


def test_local_storage_save_and_read() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(Path(tmpdir))

        path = storage.save("test.jpg", b"image-data")
        assert path == str(Path(tmpdir) / "test.jpg")

        # File exists
        assert storage.exists("test.jpg")
        assert not storage.exists("nonexistent.jpg")


def test_local_storage_public_url() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(Path(tmpdir))
        url = storage.get_public_url("photo.jpg")
        assert url == str(Path(tmpdir) / "photo.jpg")


# --- LocalVaultStorage ---


def test_vault_storage_save_read_delete() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalVaultStorage(Path(tmpdir))

        key = storage.save(1, "visa.pdf", b"pdf-content", "application/pdf")
        assert key.startswith("1/")
        assert key.endswith(".pdf")

        # Exists
        assert storage.exists(key)
        assert not storage.exists("1/nonexistent.pdf")

        # Read
        content = storage.read(key)
        assert content == b"pdf-content"

        # Read nonexistent
        assert storage.read("1/nonexistent.pdf") is None

        # Signed URL (local = path)
        url = storage.get_signed_url(key)
        assert url == f"/vault-files/{key}"

        # Delete
        assert storage.delete(key) is True
        assert storage.exists(key) is False
        assert storage.delete(key) is False  # already deleted


def test_vault_storage_generate_key() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalVaultStorage(Path(tmpdir))

        key1 = storage.generate_key(42, "document.pdf")
        assert key1.startswith("42/")
        assert key1.endswith(".pdf")

        # No extension
        key2 = storage.generate_key(42, "noext")
        assert key2.endswith(".bin")

        # Unique keys
        key3 = storage.generate_key(42, "document.pdf")
        assert key1 != key3


def test_vault_storage_subdirectory_creation() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalVaultStorage(Path(tmpdir))

        # Save creates user subdirectory
        key = storage.save(99, "photo.jpg", b"jpeg-data", "image/jpeg")
        assert (Path(tmpdir) / key).exists()
        assert (Path(tmpdir) / "99").is_dir()
