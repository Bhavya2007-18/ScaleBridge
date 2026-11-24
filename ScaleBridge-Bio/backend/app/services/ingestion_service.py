import csv
import io
import math
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.batch import DataFile, ColumnMapping, Batch
from app.models.measurement import Measurement, QualityIssue

class IngestionService:
    """Handles raw CSV/Excel experimental data ingestion, parsing, and quality validation."""

    def parse_and_validate_csv(
        self,
        db: Session,
        data_file_id: str,
        csv_content: str,
        batch_id: str,
        mappings: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        reader = csv.DictReader(io.StringIO(csv_content))
        mapping_dict = {m["source_column"]: m["standard_parameter"] for m in mappings}
        units_dict = {m["source_column"]: m.get("unit", "") for m in mappings}

        measurements = []
        issues = []
        row_idx = 0

        for row in reader:
            row_idx += 1
            # Infer timestamp or elapsed time
            timestamp_val = datetime.utcnow()
            for src_col, standard_param in mapping_dict.items():
                raw_val = row.get(src_col)
                if raw_val is None or raw_val.strip() == "":
                    continue

                try:
                    num_val = float(raw_val)
                    if math.isnan(num_val) or math.isinf(num_val):
                        issues.append(QualityIssue(
                            batch_id=batch_id,
                            parameter=standard_param,
                            issue_type="nan_or_inf",
                            severity="error",
                            row_number=row_idx,
                            message=f"Value for {standard_param} is NaN/Inf at line {row_idx}"
                        ))
                        continue

                    # Physical bounds check
                    if standard_param in ["ph"] and not (2.0 <= num_val <= 12.0):
                        issues.append(QualityIssue(
                            batch_id=batch_id,
                            parameter=standard_param,
                            issue_type="out_of_range",
                            severity="warning",
                            row_number=row_idx,
                            message=f"pH value {num_val} is outside typical biological range (2.0 - 12.0)"
                        ))

                    measurements.append(Measurement(
                        batch_id=batch_id,
                        parameter=standard_param,
                        timestamp=timestamp_val,
                        value_numeric=num_val,
                        unit=units_dict.get(src_col),
                        value_nature="measured",
                        provenance_source=f"data_file:{data_file_id}:line_{row_idx}"
                    ))
                except ValueError:
                    measurements.append(Measurement(
                        batch_id=batch_id,
                        parameter=standard_param,
                        timestamp=timestamp_val,
                        value_text=raw_val,
                        unit=units_dict.get(src_col),
                        value_nature="measured",
                        provenance_source=f"data_file:{data_file_id}:line_{row_idx}"
                    ))

        db.add_all(measurements)
        db.add_all(issues)
        db.commit()

        return {
            "ingested_measurements_count": len(measurements),
            "quality_issues_count": len(issues),
            "rows_processed": row_idx
        }
