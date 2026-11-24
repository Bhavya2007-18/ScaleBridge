"""Domain B — Experimental Data Ingestion, Pint Unit Normalization, and DQ-* Quality Service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ConversionRecord, Measurement, QualityIssue
from app.modules.ingestion_service import (
    preview_file_bytes,
    read_dataframe_from_bytes,
    validate_and_normalize_dataframe,
)


class IngestionService:
    """Orchestrates raw CSV/XLSX parsing, Pint unit conversion, DQ-* quality checks, and DB persistence."""

    def preview_bytes(
        self,
        raw_bytes: bytes,
        filename: str,
        sheet_name: str | None = None,
        max_rows: int = 25,
    ) -> dict[str, Any]:
        return preview_file_bytes(
            raw_bytes=raw_bytes,
            filename=filename,
            sheet_name=sheet_name,
            max_rows=max_rows,
        )

    def parse_and_validate_csv(
        self,
        db: Session,
        data_file_id: str,
        csv_content: str,
        batch_id: str,
        mappings: list[dict[str, str]],
        organization_id: str = "default",
        timestamp_column: str = "elapsed_h",
        timestamp_kind: str = "elapsed",
        elapsed_unit: str = "h",
    ) -> dict[str, Any]:
        raw_bytes = csv_content.encode("utf-8")
        df, _ = read_dataframe_from_bytes(raw_bytes, filename="upload.csv")

        canonical_mapping: dict[str, Any] = {
            "timestamp": {
                "column": timestamp_column if timestamp_column in df.columns else (str(df.columns[0]) if len(df.columns) > 0 else "time"),
                "kind": timestamp_kind,
                "elapsed_unit": elapsed_unit,
            },
            "batch_start": datetime.now(timezone.utc).isoformat(),
            "columns": [
                {
                    "source": m.get("source_column") or m.get("source"),
                    "variable": m.get("standard_parameter") or m.get("variable"),
                    "unit": m.get("unit", ""),
                    "provenance": m.get("provenance", "sensor"),
                    "sensor_or_assay": m.get("sensor_or_assay"),
                    "calibration_status": m.get("calibration_status", "unknown"),
                }
                for m in mappings
            ],
        }

        report = validate_and_normalize_dataframe(df, canonical_mapping)

        if not report["blocking"]:
            measurement_rows = [
                Measurement(
                    organization_id=organization_id,
                    batch_id=batch_id,
                    ts=m["ts"],
                    elapsed_s=m["elapsed_s"],
                    variable=m["variable"],
                    value_original=m["value_original"],
                    unit_original=m["unit_original"],
                    value_si=m["value_si"],
                    unit_si=m["unit_si"],
                    provenance=m["provenance"],
                    sensor_or_assay=m["sensor_or_assay"],
                    calibration_status=m["calibration_status"],
                    quality_flag=m["quality_flag"],
                    data_file_id=data_file_id,
                    source_row=m["source_row"],
                )
                for m in report["normalized_measurements"]
            ]

            issue_rows = [
                QualityIssue(
                    organization_id=organization_id,
                    data_file_id=data_file_id,
                    batch_id=batch_id,
                    check_code=iss["check_code"],
                    severity=iss["severity"],
                    variable=iss["variable"],
                    row_start=iss["row_start"],
                    row_end=iss["row_end"],
                    count=iss["count"],
                    message=iss["message"],
                )
                for iss in report["issues"]
            ]

            conversion_rows = [
                ConversionRecord(
                    organization_id=organization_id,
                    data_file_id=data_file_id,
                    variable=c["variable"],
                    from_unit=c["from_unit"],
                    to_unit=c["to_unit"],
                    method=c["method"],
                    pint_version=c["pint_version"],
                )
                for c in report["conversions"]
            ]

            db.add_all(measurement_rows)
            db.add_all(issue_rows)
            db.add_all(conversion_rows)
            db.commit()

        return {
            "ingested_measurements_count": len(report["normalized_measurements"]),
            "quality_issues_count": len(report["issues"]),
            "rows_processed": report["rows_total"],
            "blocking": report["blocking"],
            "quality_report": report,
        }


__all__ = [
    "IngestionService",
    "preview_file_bytes",
    "read_dataframe_from_bytes",
    "validate_and_normalize_dataframe",
]
