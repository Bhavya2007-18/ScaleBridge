"""Scenario model."""

from datetime import datetime, timezone
from typing import Any
import uuid
from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def _uuid() -> str:
    return str(uuid.uuid4())

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    batch_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_vessel_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("vessel_versions.id"), nullable=False)
    target_vessel_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("vessel_versions.id"), nullable=False)
    target_working_volume_original: Mapped[float] = mapped_column(Float, nullable=False)
    target_working_volume_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    target_working_volume_si: Mapped[float] = mapped_column(Float, nullable=False)
    criteria: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    aeration_basis: Mapped[str] = mapped_column(String(16), default="S-VVM", nullable=False)
    kla_selection: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    batch_window: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    statistic_overrides: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    constraints: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    assumptions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    thresholds: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
