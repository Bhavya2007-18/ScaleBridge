from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class VesselParameterCreate(BaseModel):
    category: str
    parameter_key: str
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    is_estimated: bool = False
    source: str = "equipment_manual"

class VesselParameterRead(VesselParameterCreate):
    id: str

    model_config = ConfigDict(from_attributes=True)

class VesselBase(BaseModel):
    name: str
    facility: Optional[str] = None
    scale_category: str
    working_volume_min_l: float
    working_volume_max_l: float
    total_volume_l: float
    aspect_ratio: Optional[float] = None
    impeller_count: int = 1
    impeller_types: List[str] = []
    baffle_count: int = 4
    sparger_type: Optional[str] = None
    max_rpm: Optional[float] = None
    max_power_w: Optional[float] = None
    max_gassing_vvm: Optional[float] = None

class VesselCreate(VesselBase):
    parameters: Optional[List[VesselParameterCreate]] = []

class VesselRead(VesselBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    parameters: List[VesselParameterRead] = []

    model_config = ConfigDict(from_attributes=True)
