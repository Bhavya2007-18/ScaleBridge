"""Auth request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str


class InviteAcceptRequest(BaseModel):
    token: str
    full_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=8)


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
