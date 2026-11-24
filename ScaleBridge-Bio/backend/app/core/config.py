"""Application configuration loaded from environment variables (docs/21_DEPLOYMENT.md)."""

from __future__ import annotations

import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings.

    Secrets are never committed.  In development an ephemeral JWT secret is
    generated when ``JWT_SECRET_KEY`` is absent; production deployments must
    provide a stable secret through the environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"
    app_name: str = "ScaleBridge Bio API"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./var/scalebridge.db"
    auto_create_tables: bool = True
    seed_demo_on_startup: bool = True

    storage_backend: str = "local"  # "local" | "s3"
    local_storage_path: str = "./var/storage"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "scalebridge-files"

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7

    max_upload_mb: int = 50
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    )

    def model_post_init(self, __context: object) -> None:
        if not self.jwt_secret_key:
            if self.environment.lower() in {"production", "prod"}:
                raise ValueError(
                    "JWT_SECRET_KEY must be set when ENVIRONMENT=production"
                )
            # Development-only, per-process secret. Tokens are intentionally
            # invalidated when the development server restarts.
            self.jwt_secret_key = secrets.token_urlsafe(48)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    def ensure_dirs(self) -> None:
        Path(self.local_storage_path).mkdir(parents=True, exist_ok=True)
        if self.database_url.startswith("sqlite:///"):
            raw_path = self.database_url.removeprefix("sqlite:///")
            if raw_path and raw_path != ":memory:":
                db_path = Path(raw_path)
                if db_path.parent != Path("."):
                    db_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
