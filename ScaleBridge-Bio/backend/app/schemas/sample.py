from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class SampleCreate(BaseModel):
    batch_id: str
    sample_id: str
    timestamp: datetime
    assay_type: str
    result_numeric: Optional[float] = None
    result_text: Optional[str] = None
    unit: Optional[str] = None
    replicate_number: int = 1
    operator: Optional[str] = None
    metadata_json: Dict[str, Any] = {}

class SampleRead(SampleCreate):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
