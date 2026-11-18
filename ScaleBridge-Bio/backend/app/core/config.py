"""Application configuration loaded from environment variables (docs/21_DEPLOYMENT.md)."""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ScaleBridge Bio API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./var/scalebridge.db"
    storage_backend: str = "local"  # "local" | "s3"
    local_storage_path: str = "./var/storage"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "scalebridge-files"
    jwt_secret_key: str = "scalebridge-dev-secret-key-change-in-production-32b"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    max_upload_mb: int = 50
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    seed_demo_on_startup: bool = True

    def ensure_dirs(self) -> None:
        Path(self.local_storage_path).mkdir(parents=True, exist_ok=True)
        if self.database_url.startswith("sqlite:///./"):
            db_path = Path(self.database_url.replace("sqlite:///./", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
