"""Auth-related Pydantic schemas."""

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    user_id: str
    message: str = "Account created. Check your email to verify."


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    session_token: str
    user_id: str


class SessionResponse(BaseModel):
    user: dict
    profile: dict | None = None
