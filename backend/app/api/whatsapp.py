"""WhatsApp integration API routes (R023, R024).

Provides endpoints for connecting a WhatsApp number via WhatsApp Cloud API
and checking connection status.

PII Protection: Phone numbers are hashed (SHA-256) for lookup and encrypted
(Fernet) only when absolutely necessary. API responses NEVER expose raw phone numbers.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_supabase_client
from app.core.security import encrypt_phone, hash_phone
from app.schemas.whatsapp import (
    WhatsAppMessageRequest,
    WhatsAppConnectRequest,
    WhatsAppConnectionResponse,
    WhatsAppConfigResponse,
)

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


@router.post("/connect", response_model=WhatsAppConnectionResponse)
async def connect_whatsapp(
    body: WhatsAppConnectRequest,
    supabase: Client = Depends(_get_supabase),
):
    """Initiate WhatsApp Cloud API connection (R023).

    Stores phone hash + encrypted phone in whatsapp_connections table.
    Returns Meta opaque IDs for frontend QR generation.
    Real integration requires Meta Business Account verification.
    """
    user = _require_user(supabase)
    profile_id = _require_profile(supabase, user)

    phone = body.phone_number.strip()
    if not phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required")

    # Normalize and hash for lookup (PII protection)
    phone_hash = hash_phone(phone)
    phone_encrypted = encrypt_phone(phone)

    # Upsert connection (one per profile)
    connection_data = {
        "profile_id": profile_id,
        "phone_hash": phone_hash,
        "phone_encrypted": phone_encrypted,
        "status": "pending",
        "verified_at": None,
        # wa_business_account_id and wa_phone_number_id will be set after Meta verification
    }

    try:
        resp = supabase.table("whatsapp_connections").upsert(
            connection_data,
            on_conflict="profile_id",
        ).execute()
        connection = resp.data[0] if resp.data else None
    except Exception as e:
        logger.error("Failed to create WhatsApp connection for profile %s: %s", profile_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save connection")

    logger.info("WhatsApp connect initiated for profile %s (phone_hash=%s...)", profile_id, phone_hash[:8])

    # Return placeholder QR - in production this would be from Meta Cloud API
    # Meta returns a code that frontends render as QR for user to scan
    qr_placeholder = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=whatsapp:{phone_hash[:16]}"

    return WhatsAppConnectionResponse(
        connected=False,  # Not verified yet
        status="pending",
        wa_business_account_id=None,
        wa_phone_number_id=None,
        verified_at=None,
    )


@router.get("/status", response_model=WhatsAppConnectionResponse)
async def whatsapp_status(
    supabase: Client = Depends(_get_supabase),
):
    """Check WhatsApp connection status (R023).

    Returns connection status WITHOUT exposing phone number.
    """
    user = _require_user(supabase)
    profile_id = _require_profile(supabase, user)

    resp = supabase.table("whatsapp_connections").select(
        "status, wa_business_account_id, wa_phone_number_id, verified_at"
    ).eq("profile_id", profile_id).maybe_single().execute()

    if not resp.data:
        return WhatsAppConnectionResponse(
            connected=False,
            status="pending",
            wa_business_account_id=None,
            wa_phone_number_id=None,
            verified_at=None,
        )

    conn = resp.data
    is_verified = conn.get("status") == "verified"

    return WhatsAppConnectionResponse(
        connected=is_verified,
        status=conn.get("status", "pending"),
        wa_business_account_id=conn.get("wa_business_account_id"),
        wa_phone_number_id=conn.get("wa_phone_number_id"),
        verified_at=conn.get("verified_at"),
    )


@router.post("/webhook", response_model=dict)
async def whatsapp_webhook(
    body: WhatsAppMessageRequest,
    supabase: Client = Depends(_get_supabase),
):
    """Receive incoming WhatsApp messages (R024).

    Matches sender by phone_hash to find profile, then creates idea.
    Phone number from webhook is NOT stored - only used for hash lookup.
    """
    from_number = body.from_number
    if not from_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="from_number required")

    phone_hash = hash_phone(from_number)

    # Find connection by phone hash
    conn_resp = supabase.table("whatsapp_connections").select(
        "profile_id, phone_encrypted"
    ).eq("phone_hash", phone_hash).maybe_single().execute()

    if not conn_resp.data:
        logger.warning("WhatsApp webhook from unknown number (hash=%s...)", phone_hash[:8])
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Number not connected")

    profile_id = conn_resp.data["profile_id"]

    # Create idea (persist FIRST, enrich later)
    idea_data = {
        "profile_id": profile_id,
        "title": body.message.strip().split("\n")[0][:80] if body.message.strip() else "WhatsApp Idea",
        "description": body.message,
        "source": "whatsapp",
        "content_pillar": None,
        "suggested_format": None,
        "media_refs": body.media or [],
        "status": "idea",
    }

    try:
        idea_resp = supabase.table("content_ideas").insert(idea_data).execute()
        idea_id = idea_resp.data[0]["id"]
    except Exception as e:
        logger.error("Failed to persist WhatsApp idea for profile %s: %s", profile_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save idea")

    logger.info("WhatsApp idea created: %s for profile %s (hash=%s...)", idea_id, profile_id, phone_hash[:8])

    return {"id": idea_id, "status": "created"}


# Legacy endpoint (deprecated)
@router.get("/legacy/status", response_model=WhatsAppConfigResponse, deprecated=True)
async def whatsapp_legacy_status(
    supabase: Client = Depends(_get_supabase),
):
    """Legacy endpoint - returns connected status only."""
    user = _require_user(supabase)
    profile_id = _require_profile(supabase, user)

    resp = supabase.table("whatsapp_connections").select("status").eq("profile_id", profile_id).maybe_single().execute()
    is_connected = resp.data and resp.data.get("status") == "verified"

    return WhatsAppConfigResponse(
        connected=is_connected,
        phone=None,  # Never expose phone
        qr_code=None,
    )