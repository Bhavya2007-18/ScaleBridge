from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class ScenarioCreate(BaseModel):
    project_id: str
    source_vessel_id: str
    target_vessel_id: str
    target_working_volume_l: float
    selected_criteria: List[str]  # e.g., ["constant_p_v", "constant_tip_speed"]
    target_process_temperature_c: float = 37.0
    operating_parameters: Dict[str, Any] = {}
    notes: Optional[str] = None

class ScenarioRead(ScenarioCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
