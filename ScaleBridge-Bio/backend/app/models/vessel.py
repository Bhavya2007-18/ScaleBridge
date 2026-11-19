"""Bioreactor vessel, vessel version, and parameter models."""

from datetime import datetime, timezone
from typing import Any
import uuid
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def _uuid() -> str:
    return str(uuid.uuid4())

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Vessel(Base):
    __tablename__ = "vessels"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_org_vessel_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    scale_class: Mapped[str] = mapped_column(String(32), default="lab", nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class VesselVersion(Base):
    __tablename__ = "vessel_versions"
    __table_args__ = (UniqueConstraint("vessel_id", "version", name="uq_vessel_ver"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    vessel_id: Mapped[str] = mapped_column(String(36), ForeignKey("vessels.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    impeller_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    impeller_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sparger_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instrumentation: Mapped[list[str]] = mapped_column(JSON, default=list)
    controls: Mapped[list[str]] = mapped_column(JSON, default=list)
    kla_evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    mixing_time_evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

class VesselParameter(Base):
    __tablename__ = "vessel_parameters"
    __table_args__ = (UniqueConstraint("vessel_version_id", "key", name="uq_vessel_ver_param_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    vessel_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("vessel_versions.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_original: Mapped[float] = mapped_column(Float, nullable=False)
    unit_original: Mapped[str] = mapped_column(String(64), nullable=False)
    value_si: Mapped[float] = mapped_column(Float, nullable=False)
    unit_si: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance: Mapped[str] = mapped_column(String(32), nullable=False)
    value_nature: Mapped[str] = mapped_column(String(32), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
