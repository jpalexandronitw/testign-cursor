from __future__ import annotations

from fastapi import FastAPI

from app.core.config import settings
from app.db.models import Base
from app.db.session import engine, SessionLocal
from app.routers import admin, auth, items
from app.seed import seed_defaults


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            seed_defaults(db)

    @app.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(items.router)
    return app


app = create_app()

