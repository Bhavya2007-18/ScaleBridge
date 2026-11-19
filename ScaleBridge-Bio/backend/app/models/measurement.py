"""Measurement, QualityIssue, and ConversionRecord models."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def _uuid() -> str:
    return str(uuid.uuid4())

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("batches.id"), nullable=False, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    elapsed_s: Mapped[float] = mapped_column(Float, nullable=False)
    variable: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value_original: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_original: Mapped[str] = mapped_column(String(64), nullable=False)
    value_si: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_si: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance: Mapped[str] = mapped_column(String(32), default="sensor", nullable=False)
    sensor_or_assay: Mapped[str | None] = mapped_column(String(128), nullable=True)
    calibration_status: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    quality_flag: Mapped[str] = mapped_column(String(32), default="ok", nullable=False)
    data_file_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    supersedes_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

class QualityIssue(Base):
    __tablename__ = "quality_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    data_file_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_files.id"), nullable=False, index=True)
    batch_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("batches.id"), nullable=True, index=True)
    check_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    variable: Mapped[str | None] = mapped_column(String(100), nullable=True)
    row_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

class ConversionRecord(Base):
    __tablename__ = "conversion_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    data_file_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_files.id"), nullable=False, index=True)
    variable: Mapped[str] = mapped_column(String(100), nullable=False)
    from_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    to_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    method: Mapped[str] = mapped_column(String(64), default="pint", nullable=False)
    pint_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
