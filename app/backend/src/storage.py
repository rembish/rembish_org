"""Storage abstraction for local and GCS backends."""

from abc import ABC, abstractmethod
from pathlib import Path

from .config import settings


class StorageBackend(ABC):
    """Abstract storage backend."""

    @abstractmethod
    def save(self, filename: str, content: bytes) -> str:
        """Save content and return public URL or path."""
        pass

    @abstractmethod
    def get_public_url(self, filename: str) -> str:
        """Get public URL for a file."""
        pass

    @abstractmethod
    def exists(self, filename: str) -> bool:
        """Check if file exists."""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage (for development)."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes) -> str:
        path = self.base_path / filename
        path.write_bytes(content)
        return str(path)

    def get_public_url(self, filename: str) -> str:
        return str(self.base_path / filename)

    def exists(self, filename: str) -> bool:
        return (self.base_path / filename).exists()


class GCSStorage(StorageBackend):
    """Google Cloud Storage backend."""

    def __init__(self, bucket_name: str):
        from google.cloud import storage

        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def save(self, filename: str, content: bytes) -> str:
        blob = self.bucket.blob(f"instagram/{filename}")
        blob.upload_from_string(content, content_type="image/jpeg")
        return self.get_public_url(filename)

    def get_public_url(self, filename: str) -> str:
        return f"https://storage.googleapis.com/{self.bucket_name}/instagram/{filename}"

    def exists(self, filename: str) -> bool:
        blob = self.bucket.blob(f"instagram/{filename}")
        return bool(blob.exists())


def get_storage() -> StorageBackend:
    """Get configured storage backend."""
    if settings.gcs_bucket:
        return GCSStorage(settings.gcs_bucket)
    return LocalStorage(Path("/app/data/instagram"))
