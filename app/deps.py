from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_jwt_token, decode_jwt_token
from app.db.models import ApiToken, Permission, Role, User
from app.db.session import SessionLocal

bearer = HTTPBearer(auto_error=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _http_401(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _http_403(detail: str = "Not enough permissions") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def mint_access_token_for_user(user: User, db: Session) -> tuple[str, str, Any]:
    token, jti, expires_at = create_jwt_token(
        subject=str(user.id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    db.add(
        ApiToken(
            jti=jti,
            token_type="access",
            user_id=user.id,
            expires_at=expires_at,
            revoked=False,
        )
    )
    db.commit()
    return token, jti, expires_at


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _http_401()

    token = credentials.credentials
    try:
        payload = decode_jwt_token(token)
    except ValueError:
        raise _http_401("Invalid token")

    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not user_id or not jti:
        raise _http_401("Invalid token payload")

    # token must exist in DB and not be revoked (enables explicit revocation)
    tok = db.scalar(select(ApiToken).where(ApiToken.jti == jti))
    if tok is None or tok.revoked:
        raise _http_401("Token revoked or unknown")

    user = db.scalar(select(User).where(User.id == int(user_id)))
    if user is None or not user.is_active:
        raise _http_401("Inactive user")

    return user


def get_user_permissions(user: User, db: Session) -> set[str]:
    # Ensure relationships are loaded; selectin relationships make this efficient.
    perms: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            perms.add(perm.name)
    return perms


def require_permissions(*required: str) -> Callable[..., User]:
    def _dep(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if not required:
            return user
        perms = get_user_permissions(user, db)
        if "admin:manage" in perms:
            return user
        missing = [p for p in required if p not in perms]
        if missing:
            raise _http_403(f"Missing permissions: {', '.join(missing)}")
        return user

    return _dep

