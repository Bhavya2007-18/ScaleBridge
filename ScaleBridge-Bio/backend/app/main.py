"""FastAPI application factory and lifespan management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import Base, SessionLocal, engine
from app.seed.demo_data import seed_demo_data


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Prepare local resources and release them on shutdown.

    Schema creation and demo seeding are deliberately opt-in so production
    deployments can run Alembic migrations and seed explicitly.
    """
    setup_logging()
    settings.ensure_dirs()

    if settings.auto_create_tables and not settings.is_production:
        Base.metadata.create_all(bind=engine)

    if settings.seed_demo_on_startup:
        with SessionLocal() as db:
            seed_demo_data(db)

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
