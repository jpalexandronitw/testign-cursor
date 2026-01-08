from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Message(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    jti: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: datetime


class ApiKeyCreate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    expire_days: int | None = Field(default=None, ge=1, le=3650)


class PermissionCreate(BaseModel):
    name: str = Field(min_length=3, max_length=128)


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    permissions: list[str] = Field(default_factory=list)


class UserRoleAssign(BaseModel):
    roles: list[str] = Field(default_factory=list)

