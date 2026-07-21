"""Instagram OAuth routes — connect, callback, and status.

Uses Instagram Basic Display API for the OAuth flow. Tokens are encrypted
with Fernet before storage.
"""

import secrets
import uuid
import logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.config import settings
from app.core.database import get_supabase_client
from app.core.security import encrypt_token
from app.schemas.social import (
    InstagramAccountResponse,
    InstagramCallbackRequest,
    InstagramConnectRequest,
    InstagramConnectResponse,
    InstagramStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["social"])

# In-memory CSRF state store: state token -> expiry datetime
_oauth_states: dict[str, datetime] = {}


def _get_supabase() -> Client:
    return get_supabase_client()


def _require_user(supabase: Client) -> dict:
    result = supabase.auth.get_user()
    user = result.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"id": user.id, "email": user.email}


@router.post("/instagram/connect", response_model=InstagramConnectResponse)
async def instagram_connect(body: InstagramConnectRequest):
    """Initiate Instagram OAuth by returning the Meta authorization URL."""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.now(timezone.utc) + timedelta(minutes=10)
    params = {
        "client_id": settings.INSTAGRAM_CLIENT_ID,
        "redirect_uri": body.redirect_uri or settings.INSTAGRAM_REDIRECT_URI,
        "scope": "instagram_basic,instagram_content_publish,pages_read_engagement",
        "response_type": "code",
        "state": state,
    }
    auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
    return InstagramConnectResponse(auth_url=auth_url)


@router.post("/instagram/callback", response_model=InstagramAccountResponse)
async def instagram_callback(body: InstagramCallbackRequest, supabase: Client = Depends(_get_supabase)):
    """Handle the Instagram OAuth callback.

    Exchanges the authorization code for a long-lived access token, retrieves
    the Instagram business account, encrypts tokens, and stores the account.
    """
    # Validate state parameter
    if not body.state or body.state not in _oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter",
        )
    expiry = _oauth_states.pop(body.state)
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State parameter expired",
        )

    user = _require_user(supabase)

    # 1. Get profile for this user
    profile_resp = supabase.table("profiles").select("id").eq("user_id", user["id"]).maybe_single().execute()
    if not profile_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    profile_id = profile_resp.data["id"]

    # 2. Exchange code for short-lived token
    async with httpx.AsyncClient() as client:
        token_resp = await client.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "client_id": settings.INSTAGRAM_CLIENT_ID,
                "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
                "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                "code": body.code,
            },
        )
        if token_resp.status_code != 200:
            logger.error("Instagram code exchange failed: %s", token_resp.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to complete Instagram authentication. Please try again.",
            )
        token_data = token_resp.json()
        short_lived_token = token_data.get("access_token")

    # 3. Exchange short-lived for long-lived token
    async with httpx.AsyncClient() as client:
        long_resp = await client.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.INSTAGRAM_CLIENT_ID,
                "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
                "fb_exchange_token": short_lived_token,
            },
        )
        if long_resp.status_code != 200:
            logger.error("Instagram long-lived token exchange failed: %s", long_resp.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to complete Instagram authentication. Please try again.",
            )
        long_data = long_resp.json()
        long_token = long_data.get("access_token")
        expires_in = long_data.get("expires_in", 0)

    # 4. Fetch Instagram Business Account
    async with httpx.AsyncClient() as client:
        pages_resp = await client.get(
            "https://graph.facebook.com/v18.0/me/accounts",
            params={"access_token": long_token},
        )
        if pages_resp.status_code != 200:
            logger.error("Failed to fetch Facebook pages: %s", pages_resp.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch Facebook pages. Please try again.",
            )
        pages_data = pages_resp.json()
        if not pages_data.get("data"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Facebook Pages found. Ensure your Facebook account has a Page.",
            )
        # Take the first page
        page = pages_data["data"][0]
        page_id = page["id"]
        page_name = page.get("name", "Instagram Account")

        # Get Instagram Business Account ID
        ig_resp = await client.get(
            f"https://graph.facebook.com/v18.0/{page_id}",
            params={"fields": "instagram_business_account", "access_token": long_token},
        )
        ig_data = ig_resp.json()
        ig_business_id = ig_data.get("instagram_business_account", {}).get("id", page_id)

    # 5. Encrypt tokens
    encrypted_token = encrypt_token(long_token)

    # 6. Store in social_accounts (upsert by profile + platform)
    now = None  # Let DB default handle

    account_data = {
        "profile_id": profile_id,
        "platform": "instagram",
        "account_name": page_name,
        "account_id": ig_business_id,
        "access_token": encrypted_token,
        "is_active": True,
        "token_expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat() if expires_in else None,
    }

    # Check if account already exists
    existing = supabase.table("social_accounts").select("id").eq("profile_id", profile_id).eq("platform", "instagram").maybe_single().execute()
    if existing.data:
        supabase.table("social_accounts").update(account_data).eq("id", existing.data["id"]).execute()
        account_id = existing.data["id"]
    else:
        account_data["id"] = str(uuid.uuid4())
        supabase.table("social_accounts").insert(account_data).execute()
        account_id = account_data["id"]

    # Return the created/updated account
    result = supabase.table("social_accounts").select("*").eq("id", account_id).single().execute()
    return InstagramAccountResponse(**result.data)


@router.get("/instagram/status", response_model=InstagramStatusResponse)
async def instagram_status(supabase: Client = Depends(_get_supabase)):
    """Return Instagram connection status for the current user."""
    user = _require_user(supabase)

    profile_resp = supabase.table("profiles").select("id").eq("user_id", user["id"]).maybe_single().execute()
    if not profile_resp.data:
        return InstagramStatusResponse(connected=False)

    account_resp = supabase.table("social_accounts").select("*").eq("profile_id", profile_resp.data["id"]).eq("platform", "instagram").maybe_single().execute()
    if not account_resp.data:
        return InstagramStatusResponse(connected=False)

    return InstagramStatusResponse(
        connected=True,
        account=InstagramAccountResponse(**account_resp.data),
    )
