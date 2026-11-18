"""FastAPI application entrypoint for ScaleBridge Bio."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.db.models import Organization  # noqa: F401 - register all ORM models
from app.db.session import Base, SessionLocal, engine
from app.modules.seed_service import seed_demo_workspace


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo_on_startup:
        with SessionLocal() as db:
            seed_demo_workspace(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="ScaleBridge Bio — Bioprocess scale-up & intelligence decision-support API",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)
