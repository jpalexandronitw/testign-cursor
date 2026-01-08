from __future__ import annotations

import os
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "FastAPI ACL JWT")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-prod")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    access_token_expire_minutes: int = _get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    api_key_expire_days: int = _get_int("API_KEY_EXPIRE_DAYS", 365)


settings = Settings()

