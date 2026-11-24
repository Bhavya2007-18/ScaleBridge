from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class CalculationResultRead(BaseModel):
    id: str
    criterion_name: str
    output_parameter: str
    value_numeric: Optional[float] = None
    value_unit: Optional[str] = None
    provenance_classification: str
    assumptions: List[str] = []
    confidence_score: Optional[float] = None
    insufficient_evidence: bool = False
    evidence_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RiskFlagRead(BaseModel):
    id: str
    category: str
    title: str
    description: str
    severity: str
    mitigation_suggestion: Optional[str] = None
    source_metric: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CompatibilityCheckRead(BaseModel):
    id: str
    item_category: str
    parameter_name: str
    required_value: Optional[float] = None
    available_value: Optional[float] = None
    unit: Optional[str] = None
    status: str
    gap_analysis: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ValidationTaskRead(BaseModel):
    id: str
    phase: str
    task_name: str
    description: str
    success_criteria: str
    risk_addressed: Optional[str] = None
    is_completed: bool = False

    model_config = ConfigDict(from_attributes=True)

class AssessmentRead(BaseModel):
    id: str
    scenario_id: str
    overall_readiness_score: float
    status: str
    summary_markdown: Optional[str] = None
    created_at: datetime
    calculations: List[CalculationResultRead] = []
    risks: List[RiskFlagRead] = []
    compatibility_checks: List[CompatibilityCheckRead] = []
    validation_tasks: List[ValidationTaskRead] = []

    model_config = ConfigDict(from_attributes=True)
