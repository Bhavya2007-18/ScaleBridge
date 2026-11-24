from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    organism: str
    target_molecule: str
    expression_system: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectRead(ProjectBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PassportVersionRead(BaseModel):
    id: str
    project_id: str
    version_number: int
    critical_process_parameters: Dict[str, Any]
    critical_quality_attributes: Dict[str, Any]
    media_recipe: Dict[str, Any]
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
