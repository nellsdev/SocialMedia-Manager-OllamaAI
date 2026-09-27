"""WhatsApp integration schemas (R023, R024).

PII Protection: Phone numbers are NEVER returned in API responses.
Only connection status and Meta opaque IDs are exposed.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class WhatsAppMessageRequest(BaseModel):
    """Payload for the WhatsApp webhook handler (incoming message)."""

    message: str = Field(..., min_length=1, description="Message text from WhatsApp")
    media: list[str] | None = Field(None, description="Array of media URLs")
    from_number: str | None = Field(None, description="Sender's phone number (raw, not stored)")


class WhatsAppConnectRequest(BaseModel):
    """Request to initiate WhatsApp connection."""

    phone_number: str = Field(..., min_length=10, description="Phone in E.164 format, e.g. +5491112345678")


class WhatsAppConnectionResponse(BaseModel):
    """WhatsApp connection status (NO phone number exposed)."""

    connected: bool
    status: str  # pending, verified, revoked
    wa_business_account_id: str | None = None
    wa_phone_number_id: str | None = None
    verified_at: datetime | None = None
    # NOTE: phone number intentionally omitted for privacy


class WhatsAppConfigResponse(BaseModel):
    """Legacy response (deprecated, kept for compat)."""

    connected: bool
    phone: str | None = None  # DEPRECATED: always None
    qr_code: str | None = None