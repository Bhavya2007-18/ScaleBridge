"""Project and Process Passport models."""

from datetime import datetime, timezone
from typing import Any
import uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def _uuid() -> str:
    return str(uuid.uuid4())

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_org_project_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_family: Mapped[str | None] = mapped_column(String(100), nullable=True)
    organism_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    strain_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    process_type: Mapped[str] = mapped_column(String(32), default="fed_batch", nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    is_synthetic_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class PassportVersion(Base):
    __tablename__ = "passport_versions"
    __table_args__ = (UniqueConstraint("project_id", "version", name="uq_project_passport_ver"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    recipe_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    process_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organism_context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    medium_context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    process_parameters: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    material_context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
