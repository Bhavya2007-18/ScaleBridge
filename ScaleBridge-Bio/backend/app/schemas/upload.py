"""File upload and ingestion schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DataFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    status: str
    is_synthetic: bool
    uploaded_at: datetime
    last_quality_report: dict[str, Any] | None


class ColumnMappingCreate(BaseModel):
    name: str | None = None
    is_template: bool = False
    mapping: dict[str, Any]


class ColumnMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    data_file_id: str
    name: str | None
    mapping: dict[str, Any]
    created_at: datetime


class DryRunResponse(BaseModel):
    rows_parsed: int
    quality_issues: list[dict[str, Any]]
    sample_rows: list[dict[str, Any]]
    can_import: bool


class ImportResponse(BaseModel):
    batch_id: str
    measurements_imported: int
    samples_imported: int
    quality_issues_count: int
    conversion_records_count: int
