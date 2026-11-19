from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine
from app.api.v1.router import router as api_v1_router
from app.seed.demo_data import seed_demo_data
from app.db.session import SessionLocal

# Setup logging
setup_logging()

# Initialize tables
Base.metadata.create_all(bind=engine)

# Seed synthetic demo data
with SessionLocal() as db:
    seed_demo_data(db)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
