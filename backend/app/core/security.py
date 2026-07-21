"""Fernet-based symmetric encryption for OAuth token storage.

Access tokens and refresh tokens are encrypted at rest using a secret key
configured via `FERNET_SECRET_KEY` in Settings. The encrypted blob is stored
as a base64 string in the database; only server-side code can decrypt it
(social_accounts.access_token has column-level RLS restricting reads).
"""

from cryptography.fernet import Fernet

from app.core.config import settings


def _get_fernet() -> Fernet:
    """Return a Fernet cipher using the configured secret key."""
    return Fernet(settings.fernet_key_bytes)


def encrypt_token(plain_text: str) -> str:
    """Encrypt a plain-text token to a base64-encoded cipher string."""
    cipher = _get_fernet()
    return cipher.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_token(cipher_text: str) -> str:
    """Decrypt a base64-encoded cipher string back to plain text."""
    cipher = _get_fernet()
    return cipher.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
