from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Permission, Role, User
from app.deps import get_db, require_permissions
from app.schemas import Message, PermissionCreate, RoleCreate, UserRoleAssign

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/permissions", response_model=Message, dependencies=[Depends(require_permissions("admin:manage"))])
def create_permission(payload: PermissionCreate, db: Session = Depends(get_db)) -> Message:
    db.add(Permission(name=payload.name))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Permission already exists")
    return Message(message="created")


@router.post("/roles", response_model=Message, dependencies=[Depends(require_permissions("admin:manage"))])
def create_role(payload: RoleCreate, db: Session = Depends(get_db)) -> Message:
    perms = []
    if payload.permissions:
        perms = list(db.scalars(select(Permission).where(Permission.name.in_(payload.permissions))).all())
        found = {p.name for p in perms}
        missing = [p for p in payload.permissions if p not in found]
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown permissions: {', '.join(missing)}")

    role = Role(name=payload.name)
    role.permissions = perms
    db.add(role)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Role already exists")
    return Message(message="created")


@router.post("/users/{user_id}/roles", response_model=Message, dependencies=[Depends(require_permissions("admin:manage"))])
def assign_roles(user_id: int, payload: UserRoleAssign, db: Session = Depends(get_db)) -> Message:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    roles = []
    if payload.roles:
        roles = list(db.scalars(select(Role).where(Role.name.in_(payload.roles))).all())
        found = {r.name for r in roles}
        missing = [r for r in payload.roles if r not in found]
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown roles: {', '.join(missing)}")

    user.roles = roles
    db.add(user)
    db.commit()
    return Message(message="updated")

