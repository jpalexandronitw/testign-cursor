from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_jwt_token, hash_password, verify_password
from app.db.models import ApiToken, Role, User
from app.deps import get_current_user, get_db, mint_access_token_for_user, require_permissions
from app.schemas import ApiKeyCreate, Message, TokenResponse, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bootstrap", response_model=UserOut)
def bootstrap_admin(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    # Only allowed when there are no users yet.
    existing = db.scalar(select(User.id).limit(1))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bootstrap already completed")

    admin_role = db.scalar(select(Role).where(Role.name == "admin"))
    if admin_role is None:
        raise HTTPException(status_code=500, detail="Default roles not seeded")

    user = User(username=payload.username, password_hash=hash_password(payload.password), is_active=True)
    user.roles = [admin_role]
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, username=user.username, is_active=user.is_active, created_at=user.created_at)


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    user_role = db.scalar(select(Role).where(Role.name == "user"))
    if user_role is None:
        raise HTTPException(status_code=500, detail="Default roles not seeded")

    user = User(username=payload.username, password_hash=hash_password(payload.password), is_active=True)
    user.roles = [user_role]
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists")

    db.refresh(user)
    return UserOut(id=user.id, username=user.username, is_active=user.is_active, created_at=user.created_at)


@router.post("/token", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == form.username))
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    token, jti, expires_at = mint_access_token_for_user(user, db)
    return TokenResponse(access_token=token, expires_at=expires_at, jti=jti)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, username=user.username, is_active=user.is_active, created_at=user.created_at)


@router.post("/api-keys", response_model=TokenResponse)
def create_api_key(
    body: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TokenResponse:
    expire_days = body.expire_days or settings.api_key_expire_days
    token, jti, expires_at = create_jwt_token(
        subject=str(user.id),
        token_type="api_key",
        expires_delta=timedelta(days=expire_days),
    )
    db.add(
        ApiToken(
            jti=jti,
            token_type="api_key",
            name=body.name,
            user_id=user.id,
            expires_at=expires_at,
            revoked=False,
        )
    )
    db.commit()
    return TokenResponse(access_token=token, expires_at=expires_at, jti=jti)


@router.post("/api-keys/revoke/{jti}", response_model=Message)
def revoke_api_key(
    jti: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    tok = db.scalar(select(ApiToken).where(ApiToken.jti == jti))
    if tok is None:
        raise HTTPException(status_code=404, detail="Token not found")
    if tok.token_type != "api_key":
        raise HTTPException(status_code=400, detail="Not an API key token")

    # owner or admin can revoke
    if tok.user_id != user.id:
        # If not owner, require admin permission.
        _ = require_permissions("admin:manage")(user=user, db=db)

    tok.revoked = True
    db.add(tok)
    db.commit()
    return Message(message="revoked")

