from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ValueNature(str, Enum):
    MEASURED = "measured"
    CALCULATED = "calculated"
    ESTIMATED = "estimated"
    ASSUMED = "assumed"
    DEFAULT = "default"

class ProvenanceRecord(BaseModel):
    value_nature: ValueNature
    source_reference: str
    assumptions: List[str] = []
    confidence_score: float = 1.0
    insufficient_evidence: bool = False
    notes: Optional[str] = None
    input_parameters: Dict[str, Any] = {}
