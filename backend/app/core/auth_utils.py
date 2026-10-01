"""Authentication helpers — Bearer token extraction and user resolution.

supabase-py does NOT read the ``Authorization`` header from the incoming
request automatically; the JWT must be passed explicitly to
``supabase.auth.get_user(jwt)``. These helpers centralize that handling
so every router resolves the user from the request's bearer token.
"""

from fastapi import HTTPException, Request, status
from supabase import Client


def extract_bearer_token(request: Request) -> str:
    """Return the raw bearer token from the Authorization header.

    Strips the ``Bearer `` prefix when present. Returns an empty string
    when the header is absent.
    """
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return authorization[len("Bearer "):]
    return authorization


def require_user(request: Request, supabase: Client) -> dict:
    """Resolve the authenticated user from the request's bearer token.

    Raises HTTPException(401) when the token is missing or does not
    resolve to a user.
    """
    token = extract_bearer_token(request)
    result = supabase.auth.get_user(token)
    user = result.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"id": str(user.id), "email": user.email}


def require_profile(supabase: Client, user_id: str) -> str:
    """Resolve the profile_id for an authenticated user.

    Raises HTTPException(404) when the user has no profile yet.
    """
    profile = maybe_single_data(
        supabase.table("profiles").select("id").eq("user_id", user_id)
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile["id"]


def maybe_single_data(table_query, default=None):
    """Execute a Supabase `.maybe_single()` query safely.

    supabase-py v2 returns None from ``execute()`` when no rows match
    (instead of an object with ``.data``). This helper normalizes that:
    returns the row dict, or ``default`` (None) when no row exists.

    Usage:
        row = maybe_single_data(
            supabase.table("profiles").select("*").eq("user_id", uid)
        )
    """
    result = table_query.maybe_single().execute()
    if result is None:
        return default
    return result.data or default
