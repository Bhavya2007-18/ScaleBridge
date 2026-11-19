"""Offline sample and assay model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def _uuid() -> str:
    return str(uuid.uuid4())

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("batches.id"), nullable=False, index=True)
    sample_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    elapsed_s: Mapped[float] = mapped_column(Float, nullable=False)
    assay_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    analyte: Mapped[str] = mapped_column(String(100), nullable=False)
    method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    result_original: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_original: Mapped[str] = mapped_column(String(64), nullable=False)
    result_si: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_si: Mapped[str] = mapped_column(String(64), nullable=False)
    quality_flag: Mapped[str] = mapped_column(String(32), default="ok", nullable=False)
    data_file_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
