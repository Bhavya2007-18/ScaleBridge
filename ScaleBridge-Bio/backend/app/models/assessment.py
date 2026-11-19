"""Assessment, CalculationResult, CompatibilityCheck, RiskFlag, and ValidationTask models."""

from datetime import datetime, timezone
from typing import Any
import uuid
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def _uuid() -> str:
    return str(uuid.uuid4())

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    scenario_id: Mapped[str] = mapped_column(String(36), ForeignKey("scenarios.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(32), nullable=False)
    formula_registry_version: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_registry_version: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pint_version: Mapped[str] = mapped_column(String(32), nullable=False)
    inputs_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    trade_offs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

class CalculationResultRow(Base):
    __tablename__ = "calculation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    formula_id: Mapped[str] = mapped_column(String(32), nullable=False)
    formula_name: Mapped[str] = mapped_column(String(200), nullable=False)
    formula_version: Mapped[str] = mapped_column(String(32), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    scale: Mapped[str] = mapped_column(String(16), nullable=False)
    criterion_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    equation: Mapped[str] = mapped_column(String(255), nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    missing_inputs: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_level: Mapped[str] = mapped_column(String(32), nullable=False)
    assumptions: Mapped[list[str]] = mapped_column(JSON, default=list)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

class RiskFlagRow(Base):
    __tablename__ = "risk_flags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    input_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    evidence_gap: Mapped[str | None] = mapped_column(Text, nullable=True)
    threshold_used: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    validation_task_codes: Mapped[list[str]] = mapped_column(JSON, default=list)

class CompatibilityCheckRow(Base):
    __tablename__ = "compatibility_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    check_id: Mapped[str] = mapped_column(String(32), nullable=False)
    criterion_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    parameter_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    required_value_si: Mapped[float | None] = mapped_column(Float, nullable=True)
    capability_min_si: Mapped[float | None] = mapped_column(Float, nullable=True)
    capability_max_si: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_si: Mapped[str] = mapped_column(String(64), nullable=False)
    display_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    required_display: Mapped[float | None] = mapped_column(Float, nullable=True)
    capability_min_display: Mapped[float | None] = mapped_column(Float, nullable=True)
    capability_max_display: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    input_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

class ValidationTaskRow(Base):
    __tablename__ = "validation_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    task_code: Mapped[str] = mapped_column(String(64), nullable=False)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    linked_risk_flag_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    linked_check_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    waived_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
