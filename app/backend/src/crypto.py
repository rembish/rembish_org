import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import settings

_NONCE_SIZE = 12
_KEY_SIZE = 32


def _get_key() -> bytes:
    """Decode the base64-encoded 32-byte encryption key from settings."""
    raw = base64.b64decode(settings.vault_encryption_key)
    if len(raw) != _KEY_SIZE:
        raise ValueError(f"VAULT_ENCRYPTION_KEY must be 32 bytes, got {len(raw)}")
    return raw


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


def mask_value(value: str) -> str:
    """Mask a value showing first 2 and last 2 chars. Short values fully masked."""
    if len(value) <= 4:
        return "\u2022" * len(value)
    return value[:2] + "\u2022" * (len(value) - 4) + value[-2:]
