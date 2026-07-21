"""Application configuration via Pydantic Settings.

Loads environment variables and secrets. All sensitive values default to
dev-only placeholders — override via .env or environment variables in prod.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Social Media Manager"
    DEBUG: bool = False

    # --- Supabase ---
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_SERVICE_KEY: str = "dev-service-key"
    SUPABASE_ANON_KEY: str = "dev-anon-key"

    # --- JWT (Supabase Auth) ---
    SUPABASE_JWT_SECRET: str = "dev-jwt-secret-change-in-prod"

    # --- Fernet encryption (token storage) ---
    FERNET_SECRET_KEY: str = ""

    # --- WhatsApp webhook verification ---
    WHATSAPP_WEBHOOK_SECRET: str = ""

    # --- Instagram / Meta Graph API ---
    INSTAGRAM_CLIENT_ID: str = ""
    INSTAGRAM_CLIENT_SECRET: str = ""
    INSTAGRAM_REDIRECT_URI: str = "http://localhost:8000/api/social/instagram/callback"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- Scheduling ---
    SCHEDULER_DB_URL: str = "sqlite:///./scheduler.db"

    @property
    def fernet_key_bytes(self) -> bytes:
        """Return the Fernet key as bytes.

        Raises RuntimeError in production if the key is not set.
        Generates a random dev key (with warning) when DEBUG is True.
        """
        if not self.FERNET_SECRET_KEY:
            if self.DEBUG:
                import secrets
                import base64
                import logging

                logging.warning(
                    "FERNET_SECRET_KEY not set — using random dev key "
                    "(DO NOT USE IN PRODUCTION)"
                )
                return base64.urlsafe_b64encode(secrets.token_bytes(32))
            raise RuntimeError("FERNET_SECRET_KEY must be set in production")
        return self.FERNET_SECRET_KEY.encode("utf-8")


settings = Settings()
