"""Auth routes — register, login, and session verification.

All routes rely on Supabase Auth for credential handling and JWT issuance.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from app.core.auth_utils import extract_bearer_token
from app.core.database import get_supabase_client
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    SessionResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)


def _get_supabase() -> Client:
    return get_supabase_client()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, supabase: Client = Depends(_get_supabase)):
    """Register a new user via email/password through Supabase Auth."""
    try:
        result = supabase.auth.sign_up({"email": body.email, "password": body.password})
        return RegisterResponse(
            user_id=result.user.id if result.user else "",
            message="Account created. Check your email to verify.",
        )
    except Exception as exc:
        logger.exception("Registration failed")
        if "already registered" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try again.",
        )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, supabase: Client = Depends(_get_supabase)):
    """Authenticate user and return a session token."""
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        session = result.session
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return LoginResponse(
            session_token=session.access_token,
            user_id=result.user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@router.get("/session", response_model=SessionResponse)
async def get_session(request: Request, supabase: Client = Depends(_get_supabase)):
    """Verify the current session and return user + profile data.

    Requires a Bearer token in the Authorization header. The token is
    extracted from the request and passed explicitly to supabase-py,
    which validates it via the anon key.
    """
    try:
        result = supabase.auth.get_user(extract_bearer_token(request))
        user = result.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid session",
            )
        # Attempt to fetch the profile
        from app.core.auth_utils import maybe_single_data
        profile_data = maybe_single_data(
            supabase.table("profiles").select("*").eq("user_id", user.id)
        )

        return SessionResponse(
            user={"id": user.id, "email": user.email},
            profile=profile_data,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
