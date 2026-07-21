"""WhatsApp integration API routes (R023, 4.5).

Provides endpoints for connecting a WhatsApp number and checking connection
status. For MVP, this is a lightweight integration — real WhatsApp Cloud API
webhook verification and message receiving will require Meta Business
verification.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_supabase_client
from app.schemas.whatsapp import WhatsAppConfigResponse, WhatsAppMessageRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


def _get_supabase() -> Client:
    return get_supabase_client()


def _require_user(supabase: Client) -> dict:
    result = supabase.auth.get_user()
    user = result.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"id": user.id, "email": user.email}


def _require_profile(supabase: Client, user: dict) -> str:
    resp = supabase.table("profiles").select("id").eq("user_id", user["id"]).maybe_single().execute()
    if not resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return resp.data["id"]


@router.post("/connect", response_model=WhatsAppConfigResponse)
async def connect_whatsapp(
    body: WhatsAppMessageRequest,
    supabase: Client = Depends(_get_supabase),
):
    """Initiate WhatsApp connection (R023).

    For MVP this stores the phone number and returns a placeholder message.
    Real WhatsApp Cloud API integration requires a Meta Business Account and
    app review.
    """
    user = _require_user(supabase)
    profile_id = _require_profile(supabase, user)

    # Store WhatsApp number in profile settings
    phone = body.from_number or ""
    if not phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required")

    # For MVP, store in a simple profile field or return a placeholder
    # In production this would initiate WhatsApp Cloud API onboarding
    supabase.table("profiles").update({
        "whatsapp_phone": phone,
    }).eq("id", profile_id).execute()

    logger.info("WhatsApp connect initiated for profile %s with phone %s", profile_id, phone)

    # Return a placeholder QR code URL for MVP
    qr_placeholder = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=whatsapp:{phone}"

    return WhatsAppConfigResponse(
        connected=True,
        phone=phone,
        qr_code=qr_placeholder,
    )


@router.get("/status", response_model=WhatsAppConfigResponse)
async def whatsapp_status(
    supabase: Client = Depends(_get_supabase),
):
    """Check WhatsApp connection status (R023)."""
    user = _require_user(supabase)
    profile_id = _require_profile(supabase, user)

    resp = supabase.table("profiles").select("whatsapp_phone").eq("id", profile_id).maybe_single().execute()
    phone = resp.data.get("whatsapp_phone") if resp.data else None

    return WhatsAppConfigResponse(
        connected=bool(phone),
        phone=phone,
    )



