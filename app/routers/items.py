from __future__ import annotations

from fastapi import APIRouter, Depends

from app.db.models import User
from app.deps import require_permissions
from app.schemas import Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[str])
def list_items(_: User = Depends(require_permissions("items:read"))) -> list[str]:
    return ["alpha", "bravo", "charlie"]


@router.post("", response_model=Message)
def create_item(_: User = Depends(require_permissions("items:write"))) -> Message:
    return Message(message="created")

