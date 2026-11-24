from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class ReviewSignoffCreate(BaseModel):
    role: str
    status: str
    comment: Optional[str] = None

class ReviewSignoffRead(ReviewSignoffCreate):
    id: str
    report_id: str
    user_id: str
    signed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReportRead(BaseModel):
    id: str
    assessment_id: str
    format: str
    title: str
    storage_path: Optional[str] = None
    summary_markdown: str
    sections: Dict[str, Any]
    provenance_hash: Optional[str] = None
    created_at: datetime
    signoffs: List[ReviewSignoffRead] = []

    model_config = ConfigDict(from_attributes=True)
