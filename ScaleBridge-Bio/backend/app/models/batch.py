"""Batch and Ingested Data File models."""

from datetime import datetime, timezone
from typing import Any
import uuid
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def _uuid() -> str:
    return str(uuid.uuid4())

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class DataFile(Base):
    __tablename__ = "data_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_description: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_quality_report: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

class ColumnMapping(Base):
    __tablename__ = "column_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    data_file_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_files.id"), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mapping: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = (UniqueConstraint("project_id", "run_code", name="uq_project_run_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    passport_version_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("passport_versions.id"), nullable=True)
    vessel_version_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vessel_versions.id"), nullable=True)
    data_file_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("data_files.id"), nullable=True)
    run_code: Mapped[str] = mapped_column(String(100), nullable=False)
    scale_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    working_volume_original: Mapped[float | None] = mapped_column(Float, nullable=True)
    working_volume_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    working_volume_si: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operator: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
