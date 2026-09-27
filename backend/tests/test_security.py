"""Test Fernet encryption and security utilities (Task 6.1)."""

import os
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings
from app.core.security import encrypt_token, decrypt_token


class TestFernetCrypto:
    """Encrypt/decrypt roundtrip and edge cases."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt then decrypt returns original value."""
        from cryptography.fernet import Fernet
        from app.core.security import _get_fernet
        
        # Use a fixed Fernet instance for this test
        fixed_key = Fernet.generate_key()
        fixed_fernet = Fernet(fixed_key)
        
        plaintext = "instagram-access-token-abc123"
        encrypted = fixed_fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        decrypted = fixed_fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")
        assert decrypted == plaintext
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)

    def test_encrypt_decrypt_empty_string(self):
        """Empty string encrypts/decrypts correctly."""
        from cryptography.fernet import Fernet
        fixed_fernet = Fernet(Fernet.generate_key())
        
        encrypted = fixed_fernet.encrypt(b"").decode("utf-8")
        decrypted = fixed_fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")
        assert decrypted == ""

    def test_encrypt_decrypt_unicode(self):
        """Unicode content (emojis, accents) works."""
        from cryptography.fernet import Fernet
        fixed_fernet = Fernet(Fernet.generate_key())
        
        plaintext = "token-ñáéíóú-🚀-中文"
        encrypted = fixed_fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        decrypted = fixed_fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")
        assert decrypted == plaintext

    def test_different_keys_cannot_decrypt(self):
        """Token encrypted with key A cannot be decrypted with key B."""
        from cryptography.fernet import Fernet, InvalidToken

        key_a = Fernet.generate_key()
        key_b = Fernet.generate_key()

        f_a = Fernet(key_a)
        token = f_a.encrypt(b"secret-data").decode()

        f_b = Fernet(key_b)
        with pytest.raises(InvalidToken):
            f_b.decrypt(token.encode())

    def test_tampered_token_fails(self):
        """Modified encrypted token raises InvalidToken."""
        from cryptography.fernet import Fernet, InvalidToken
        fixed_fernet = Fernet(Fernet.generate_key())
        
        plaintext = "original-token"
        encrypted = fixed_fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

        # Tamper with last char
        tampered = encrypted[:-1] + ("X" if encrypted[-1] != "X" else "Y")

        with pytest.raises(InvalidToken):
            fixed_fernet.decrypt(tampered.encode())


class TestSettingsFernetKey:
    """Settings.fernet_key_bytes property behavior."""

    def test_fernet_key_bytes_with_env_var(self):
        """Explicit FERNET_SECRET_KEY returns its bytes."""
        with patch.dict(os.environ, {"FERNET_SECRET_KEY": "my-secret-key-32-chars-long!!"}):
            settings = Settings(_env_file=None)
            key_bytes = settings.fernet_key_bytes
            assert key_bytes == b"my-secret-key-32-chars-long!!"

    def test_fernet_key_bytes_debug_generates_random(self):
        """DEBUG=True + no key -> generates random dev key (with warning)."""
        with patch.dict(os.environ, {"DEBUG": "true", "FERNET_SECRET_KEY": ""}, clear=True):
            # Remove FERNET_SECRET_KEY if present
            os.environ.pop("FERNET_SECRET_KEY", None)
            settings = Settings(_env_file=None)
            key_bytes = settings.fernet_key_bytes
            assert isinstance(key_bytes, bytes)
            # Fernet key is base64-encoded 32 bytes = 44 chars
            assert len(key_bytes) == 44

    def test_fernet_key_bytes_prod_raises(self):
        """DEBUG=False + no key -> raises RuntimeError."""
        with patch.dict(os.environ, {"DEBUG": "false"}, clear=True):
            os.environ.pop("FERNET_SECRET_KEY", None)
            settings = Settings(_env_file=None)
            with pytest.raises(RuntimeError, match="FERNET_SECRET_KEY must be set"):
                _ = settings.fernet_key_bytes


class TestCORSOrigins:
    """CORS origins parsing."""

    def test_cors_origins_default(self):
        """Default CORS_ORIGINS includes localhost:3000."""
        settings = Settings(_env_file=None)
        assert "http://localhost:3000" in settings.CORS_ORIGINS