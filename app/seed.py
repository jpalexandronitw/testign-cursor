from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Permission, Role


DEFAULT_PERMISSIONS = [
    "admin:manage",
    "items:read",
    "items:write",
]

DEFAULT_ROLES: dict[str, list[str]] = {
    "admin": DEFAULT_PERMISSIONS,
    "user": ["items:read"],
}


def seed_defaults(db: Session) -> None:
    # Permissions
    existing_perms = set(db.scalars(select(Permission.name)).all())
    for p in DEFAULT_PERMISSIONS:
        if p not in existing_perms:
            db.add(Permission(name=p))
    db.commit()

    perms_by_name = {p.name: p for p in db.scalars(select(Permission)).all()}

    # Roles + role-permission links
    for role_name, perm_names in DEFAULT_ROLES.items():
        role = db.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            role = Role(name=role_name)
            db.add(role)
            db.commit()
            db.refresh(role)

        desired = {perms_by_name[n] for n in perm_names if n in perms_by_name}
        current = set(role.permissions)
        if desired != current:
            role.permissions = list(desired)
            db.add(role)
            db.commit()

