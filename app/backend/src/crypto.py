import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import settings

_NONCE_SIZE = 12
_KEY_SIZE = 32

# Lazy-decoded key — decoded once on first use, re-decoded if settings change
_cached_key: bytes | None = None
_cached_raw: str = ""


def _get_key() -> bytes:
    """Return the base64-decoded 32-byte encryption key (cached after first call)."""
    global _cached_key, _cached_raw
    raw = settings.vault_encryption_key
    if not raw:
        raise ValueError("VAULT_ENCRYPTION_KEY is not configured")
    if raw != _cached_raw:
        _cached_key = base64.b64decode(raw)
        if len(_cached_key) != _KEY_SIZE:
            raise ValueError(f"VAULT_ENCRYPTION_KEY must be 32 bytes, got {len(_cached_key)}")
        _cached_raw = raw
    assert _cached_key is not None
    return _cached_key


def encrypt(plaintext: str) -> bytes:
    """Encrypt plaintext with AES-256-GCM. Returns nonce + ciphertext + tag."""
    key = _get_key()
    nonce = os.urandom(_NONCE_SIZE)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ct


def decrypt(data: bytes) -> str:
    """Decrypt AES-256-GCM blob (nonce + ciphertext + tag) back to plaintext."""
    key = _get_key()
    nonce = data[:_NONCE_SIZE]
    ct = data[_NONCE_SIZE:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def mask_value(value: str, max_len: int = 100) -> str:
    """Mask a value showing first 2 and last 2 chars. Long values capped."""
    if len(value) <= 4:
        return "\u2022" * len(value)
    # Cap the total masked length to max_len
    masked_len = min(len(value), max_len)
    return value[:2] + "\u2022" * (masked_len - 4) + value[-2:]
