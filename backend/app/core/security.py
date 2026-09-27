"""Fernet-based symmetric encryption for OAuth token storage and PII protection.

Access tokens, refresh tokens, and sensitive PII (phone numbers) are encrypted
at rest using a secret key configured via `FERNET_SECRET_KEY` in Settings.
The encrypted blob is stored as a base64 string in the database; only
server-side code can decrypt it (RLS policies restrict reads).
"""

import hashlib
import re

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


# ---------------------------------------------------------------------------
# Phone number protection (WhatsApp PII handling)
# ---------------------------------------------------------------------------

_PHONE_DIGITS_ONLY = re.compile(r"\D")


def normalize_phone(phone: str) -> str:
    """Normalize phone to digits only (E.164 without +).

    Examples:
        "+54 9 11 1234-5678" -> "5491112345678"
        "5491112345678" -> "5491112345678"
    """
    return _PHONE_DIGITS_ONLY.sub("", phone)


def hash_phone(phone: str) -> str:
    """SHA-256 hash of normalized phone for lookup without storing raw PII.

    Use this for: verifying ownership, deduplication, webhook matching.
    """
    normalized = normalize_phone(phone)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def encrypt_phone(phone: str) -> str:
    """Encrypt a phone number for storage (when you MUST retain it for webhooks).

    Use sparingly. Prefer hash_phone() for lookups.
    """
    return encrypt_token(phone)


def decrypt_phone(cipher_text: str) -> str:
    """Decrypt a phone number from storage."""
    return decrypt_token(cipher_text)


def verify_phone_hash(phone: str, stored_hash: str) -> bool:
    """Constant-time verification of phone against stored hash."""
    return hash_phone(phone) == stored_hash
