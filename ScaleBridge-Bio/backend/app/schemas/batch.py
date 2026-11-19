from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class DataFileRead(BaseModel):
    id: str
    tenant_id: str
    filename: str
    format: str
    row_count: int
    column_count: int
    storage_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ColumnMappingCreate(BaseModel):
    source_column: str
    standard_parameter: str
    unit: str
    data_type: str = "float"

class ColumnMappingRead(ColumnMappingCreate):
    id: str
    data_file_id: str

    model_config = ConfigDict(from_attributes=True)

class BatchCreate(BaseModel):
    batch_name: str
    vessel_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    scale_type: str = "lab"
    metadata_json: Dict[str, Any] = {}

class BatchRead(BatchCreate):
    id: str
    project_id: str
    data_file_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
