"""Social account / OAuth schemas."""

from datetime import datetime

from pydantic import BaseModel


class InstagramConnectRequest(BaseModel):
    redirect_uri: str


class InstagramConnectResponse(BaseModel):
    auth_url: str


class InstagramCallbackRequest(BaseModel):
    code: str
    state: str | None = None


class InstagramAccountResponse(BaseModel):
    id: str
    platform: str
    account_name: str
    account_id: str
    is_active: bool
    token_expires_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class InstagramStatusResponse(BaseModel):
    connected: bool
    account: InstagramAccountResponse | None = None
