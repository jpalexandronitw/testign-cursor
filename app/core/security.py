from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def new_jti() -> str:
    # 128-bit urlsafe token
    return secrets.token_urlsafe(16)


def create_jwt_token(*, subject: str, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    issued_at = now_utc()
    expire = issued_at + expires_delta
    jti = new_jti()
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(issued_at.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded, jti, expire


def decode_jwt_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("Invalid token") from e
    return payload

