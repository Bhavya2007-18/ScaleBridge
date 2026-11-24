"""SQLAlchemy 2.0 ORM models implementing docs/07_DATABASE_SCHEMA.md."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    data_retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="scientist")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="scientist")
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invited_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_org_project_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
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
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
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


class Vessel(Base):
    __tablename__ = "vessels"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_org_vessel_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
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
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    vessel_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vessels.id"), nullable=False, index=True
    )
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
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    vessel_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vessel_versions.id"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_original: Mapped[float] = mapped_column(Float, nullable=False)
    unit_original: Mapped[str] = mapped_column(String(64), nullable=False)
    value_si: Mapped[float] = mapped_column(Float, nullable=False)
    unit_si: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance: Mapped[str] = mapped_column(String(32), nullable=False)
    value_nature: Mapped[str] = mapped_column(String(32), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataFile(Base):
    __tablename__ = "data_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
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
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    data_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_files.id"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mapping: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ConversionRecord(Base):
    __tablename__ = "conversion_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    data_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_files.id"), nullable=False, index=True
    )
    variable: Mapped[str] = mapped_column(String(100), nullable=False)
    from_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    to_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    method: Mapped[str] = mapped_column(String(64), default="pint", nullable=False)
    pint_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class QualityIssue(Base):
    __tablename__ = "quality_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    data_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_files.id"), nullable=False, index=True
    )
    batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("batches.id"), nullable=True, index=True
    )
    check_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    variable: Mapped[str | None] = mapped_column(String(100), nullable=True)
    row_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = (UniqueConstraint("project_id", "run_code", name="uq_project_run_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    passport_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("passport_versions.id"), nullable=True
    )
    vessel_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vessel_versions.id"), nullable=True
    )
    data_file_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("data_files.id"), nullable=True
    )
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


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batches.id"), nullable=False, index=True
    )
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


class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batches.id"), nullable=False, index=True
    )
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


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    batch_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_vessel_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vessel_versions.id"), nullable=False
    )
    target_vessel_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vessel_versions.id"), nullable=False
    )
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


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    scenario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenarios.id"), nullable=False, index=True
    )
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
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=False, index=True
    )
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
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=False, index=True
    )
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
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=False, index=True
    )
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
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=False, index=True
    )
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


class ReviewSignoff(Base):
    __tablename__ = "review_signoffs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=False, index=True
    )
    reviewer_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    reviewer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ReportRow(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("assessment_id", "version", name="uq_assessment_rep_ver"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="generated", nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    template_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
