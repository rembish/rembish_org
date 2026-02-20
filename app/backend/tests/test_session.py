"""Unit tests for auth session/token functions.

Pure unit tests — no DB, no TestClient. Direct function calls only.
"""

from src.auth.session import (
    create_session_token,
    create_vault_token,
    verify_session_token,
    verify_vault_token,
)


class TestSessionToken:
    """Tests for create_session_token / verify_session_token."""

    def test_roundtrip(self) -> None:
        """Create a session token and verify it returns the original payload."""
        token = create_session_token(user_id=42)
        data = verify_session_token(token)
        assert data is not None
        assert data["user_id"] == 42

    def test_contains_correct_user_id(self) -> None:
        """Session token payload contains the exact user_id passed in."""
        for uid in (1, 999, 123456):
            token = create_session_token(user_id=uid)
            data = verify_session_token(token)
            assert data is not None
            assert data["user_id"] == uid

    def test_garbage_token_returns_none(self) -> None:
        """Completely invalid token string returns None."""
        assert verify_session_token("not-a-real-token") is None

    def test_tampered_token_returns_none(self) -> None:
        """A valid token with flipped characters is rejected."""
        token = create_session_token(user_id=1)
        # Flip a character in the middle of the token to break the signature
        mid = len(token) // 2
        flipped = chr(ord(token[mid]) ^ 1)
        tampered = token[:mid] + flipped + token[mid + 1 :]
        assert verify_session_token(tampered) is None


class TestVaultToken:
    """Tests for create_vault_token / verify_vault_token."""

    def test_roundtrip(self) -> None:
        """Create a vault token and verify it returns the original payload."""
        token = create_vault_token(user_id=7)
        data = verify_vault_token(token)
        assert data is not None
        assert data["user_id"] == 7

    def test_contains_user_id_and_vault_flag(self) -> None:
        """Vault token payload contains user_id and vault=True."""
        token = create_vault_token(user_id=55)
        data = verify_vault_token(token)
        assert data is not None
        assert data["user_id"] == 55
        assert data["vault"] is True

    def test_rejects_regular_session_token(self) -> None:
        """A regular session token (no vault flag) is rejected by verify_vault_token."""
        session_token = create_session_token(user_id=1)
        assert verify_vault_token(session_token) is None

    def test_garbage_token_returns_none(self) -> None:
        """Completely invalid token string returns None."""
        assert verify_vault_token("garbage.token.here") is None
