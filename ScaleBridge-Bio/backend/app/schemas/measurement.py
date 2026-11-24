from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class MeasurementRead(BaseModel):
    id: str
    batch_id: str
    parameter: str
    timestamp: datetime
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    value_nature: str
    provenance_source: str
    is_imputed: bool = False

    model_config = ConfigDict(from_attributes=True)

class QualityIssueRead(BaseModel):
    id: str
    batch_id: str
    parameter: str
    issue_type: str
    severity: str
    row_number: Optional[int] = None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BatchDataSummary(BaseModel):
    batch_id: str
    total_measurements: int
    parameters: List[str]
    time_span_hours: float
    quality_issues_count: int
