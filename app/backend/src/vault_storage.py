"""Private vault file storage with signed URL support."""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from .config import settings


class VaultStorageBackend(ABC):
    """Abstract storage backend for private vault files."""

    @abstractmethod
    def save(self, user_id: int, filename: str, content: bytes, content_type: str) -> str:
        """Save content and return storage key."""

    @abstractmethod
    def get_signed_url(self, key: str, expires_minutes: int = 15) -> str:
        """Get a time-limited signed URL for accessing the file."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a file. Returns True if deleted, False if not found."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if file exists."""

    @abstractmethod
    def read(self, key: str) -> bytes | None:
        """Read file contents (for AI extraction). Returns None if not found."""

    def generate_key(self, user_id: int, original_filename: str) -> str:
        """Generate a unique storage key: {user_id}/{uuid}.{ext}"""
        ext = Path(original_filename).suffix.lstrip(".")
        if not ext:
            ext = "bin"
        return f"{user_id}/{uuid.uuid4().hex}.{ext}"


class LocalVaultStorage(VaultStorageBackend):
    """Local filesystem storage (for development)."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, user_id: int, filename: str, content: bytes, content_type: str) -> str:
        key = self.generate_key(user_id, filename)
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        return key

    def get_signed_url(self, key: str, expires_minutes: int = 15) -> str:
        return f"/vault-files/{key}"

    def delete(self, key: str) -> bool:
        file_path = self.base_path / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def exists(self, key: str) -> bool:
        return (self.base_path / key).exists()

    def read(self, key: str) -> bytes | None:
        file_path = self.base_path / key
        if file_path.exists():
            return file_path.read_bytes()
        return None


class GCSVaultStorage(VaultStorageBackend):
    """Google Cloud Storage backend (private bucket with signed URLs).

    On Cloud Run, credentials are metadata-server tokens without a private key.
    We pass service_account_email + access_token to generate_signed_url(),
    which uses the IAM signBlob API instead of local signing.
    Requires roles/iam.serviceAccountTokenCreator on the SA.
    """

    def __init__(self, bucket_name: str):
        import google.auth
        from google.auth import compute_engine
        from google.auth.transport import requests as google_requests
        from google.cloud import storage

        self._credentials, project = google.auth.default()
        self._auth_request = google_requests.Request()

        # Detect Cloud Run (compute engine credentials without private key)
        if isinstance(self._credentials, compute_engine.Credentials):
            # Refresh to populate service_account_email (is "default" before refresh)
            self._credentials.refresh(self._auth_request)
            self._sa_email: str | None = self._credentials.service_account_email
        else:
            self._sa_email = None

        self.client = storage.Client(credentials=self._credentials, project=project)
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def save(self, user_id: int, filename: str, content: bytes, content_type: str) -> str:
        key = self.generate_key(user_id, filename)
        blob = self.bucket.blob(key)
        blob.upload_from_string(content, content_type=content_type)
        return key

    def get_signed_url(self, key: str, expires_minutes: int = 15) -> str:
        import datetime

        blob = self.bucket.blob(key)

        if self._sa_email:
            # Cloud Run: use IAM signBlob API via access_token
            self._credentials.refresh(self._auth_request)
            return str(
                blob.generate_signed_url(
                    version="v4",
                    expiration=datetime.timedelta(minutes=expires_minutes),
                    method="GET",
                    service_account_email=self._sa_email,
                    access_token=self._credentials.token,
                )
            )
        else:
            # Local with service account key file
            return str(
                blob.generate_signed_url(
                    version="v4",
                    expiration=datetime.timedelta(minutes=expires_minutes),
                    method="GET",
                )
            )

    def delete(self, key: str) -> bool:
        blob = self.bucket.blob(key)
        if blob.exists():
            blob.delete()
            return True
        return False

    def exists(self, key: str) -> bool:
        blob = self.bucket.blob(key)
        return bool(blob.exists())

    def read(self, key: str) -> bytes | None:
        blob = self.bucket.blob(key)
        if not blob.exists():
            return None
        return bytes(blob.download_as_bytes())


def get_vault_storage() -> VaultStorageBackend:
    """Get configured vault storage backend."""
    if settings.vault_gcs_bucket:
        return GCSVaultStorage(settings.vault_gcs_bucket)
    return LocalVaultStorage(Path("/app/data/vault-docs"))
