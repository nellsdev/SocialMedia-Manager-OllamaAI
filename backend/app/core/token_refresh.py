"""Instagram long-lived access token auto-refresh.

Instagram Graph API long-lived user tokens expire after ~60 days.
This module detects tokens nearing expiry and renews them via the
``ig_refresh_token`` grant before they become invalid.

Renewed tokens are encrypted with Fernet and written back to the same
``social_accounts`` row (UPDATE, never INSERT).
"""

import logging
from datetime import datetime, timezone, timedelta

import httpx

from app.core.config import settings
from app.core.security import encrypt_token

logger = logging.getLogger(__name__)

# Renew tokens when they have fewer than this many days left
REFRESH_THRESHOLD_DAYS = 7

# Instagram long-lived tokens have a fresh expiry of ~60d per refresh
REFRESHED_TOKEN_LIFETIME_DAYS = 60


async def refresh_instagram_token(access_token: str) -> dict:
    """Exchange a (still valid) long-lived token for a renewed one.

    Returns ``{"access_token": str, "expires_in": int}``.
    Raises on API error so the caller can log and continue.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            "https://graph.instagram.com/refresh_access_token",
            params={
                "grant_type": "ig_refresh_token",
                "access_token": access_token,
            },
        )
        if resp.status_code != 200:
            logger.error(
                "Instagram token refresh failed: %s — %s",
                resp.status_code,
                resp.text[:200],
            )
            raise RuntimeError(f"Instagram token refresh failed: status {resp.status_code}")

        data = resp.json()
        new_token = data.get("access_token")
        expires_in = data.get("expires_in")
        if not new_token:
            raise RuntimeError("Instagram token refresh returned no access_token")

        return {"access_token": new_token, "expires_in": expires_in}


async def maybe_refresh_token_for_account(
    supabase_client,
    account: dict,
) -> bool:
    """Refresh one social_account if its token is near expiry.

    Returns True when the account was refreshed (DB updated), False otherwise.
    Never raises: token-refresh failures are logged and skipped so they don't
    break the scheduler loop.
    """
    account_id = account.get("id")
    if not account_id:
        return False

    # Accounts without an expiry date are not managed (edge case)
    expires_at_raw = account.get("token_expires_at")
    if not expires_at_raw:
        return False

    try:
        expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        logger.warning("Unparseable token_expires_at for account %s: %s", account_id, exc)
        return False

    now = datetime.now(timezone.utc)
    if expires_at > now + timedelta(days=REFRESH_THRESHOLD_DAYS):
        return False  # Not near expiry, skip

    logger.info(
        "Token for account %s expires at %s — refreshing",
        account_id,
        expires_at.isoformat(),
    )

    try:
        from app.core.security import decrypt_token

        current_token = decrypt_token(account["access_token"])
    except Exception as exc:
        logger.error("Failed to decrypt token for account %s: %s", account_id, exc)
        return False

    try:
        refreshed = await refresh_instagram_token(current_token)
    except Exception as exc:
        logger.error("Refresh failed for account %s: %s", account_id, exc)
        return False

    new_expiry = (
        datetime.now(timezone.utc)
        + timedelta(seconds=refreshed.get("expires_in", REFRESHED_TOKEN_LIFETIME_DAYS * 86400))
    ).isoformat()

    try:
        supabase_client.table("social_accounts").update({
            "access_token": encrypt_token(refreshed["access_token"]),
            "token_expires_at": new_expiry,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", account_id).execute()
        logger.info("Refreshed token for account %s (new expiry %s)", account_id, new_expiry)
        return True
    except Exception as exc:
        logger.error("Failed to persist refreshed token for account %s: %s", account_id, exc)
        return False


async def refresh_all_near_expiry() -> int:
    """Scan all Instagram accounts and refresh tokens near expiry.

    Returns the number of accounts refreshed. Called by the periodic
    APScheduler job. Never raises (each account handled independently).
    """
    try:
        from app.core.database import get_supabase_service_client

        supabase = get_supabase_service_client()
    except Exception as exc:
        logger.error("Token refresh scan: cannot init Supabase client: %s", exc)
        return 0

    try:
        resp = (
            supabase.table("social_accounts")
            .select("*")
            .eq("platform", "instagram")
            .execute()
        )
    except Exception as exc:
        logger.error("Token refresh scan: failed to fetch accounts: %s", exc)
        return 0

    refreshed_count = 0
    for account in resp.data or []:
        if await maybe_refresh_token_for_account(supabase, account):
            refreshed_count += 1

    logger.info("Token refresh scan complete: %d account(s) refreshed", refreshed_count)
    return refreshed_count