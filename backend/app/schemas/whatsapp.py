"""WhatsApp integration schemas (R023, R024)."""

from pydantic import BaseModel, Field


class WhatsAppMessageRequest(BaseModel):
    """Payload for the WhatsApp webhook handler."""

    message: str = Field(..., min_length=1, description="Message text from WhatsApp")
    media: list[str] | None = Field(None, description="Array of media URLs")
    from_number: str | None = Field(None, description="Sender's phone number")


class WhatsAppConfigResponse(BaseModel):
    connected: bool
    phone: str | None = None
    qr_code: str | None = None
