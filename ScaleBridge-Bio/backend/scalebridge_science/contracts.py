"""Typed data contracts for `scalebridge_science` (see docs/10_SCIENTIFIC_ENGINE.md).

The public contract types are intentionally dependency-light: this module imports
only the standard library and pydantic.  ``ThresholdConfig`` is owned by
``scalebridge_science.readiness.thresholds`` and re-exported here for backwards
compatibility with existing callers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from scalebridge_science._pydantic_compat import BaseModel, Field


class Provenance(str, Enum):
    """Controlled provenance vocabulary (docs/10 §1.4, §4)."""

    sensor = "sensor"
    manual_entry = "manual_entry"
    lab_assay = "lab_assay"
    vendor_datasheet = "vendor_datasheet"
    published_correlation = "published_correlation"
    user_assumption = "user_assumption"
    calculated = "calculated"


class ValueNature(str, Enum):
    """Controlled value-nature vocabulary (docs/10 §4, §7)."""

    measured = "measured"
    estimated = "estimated"
    assumed = "assumed"
    calculated = "calculated"


EvidenceLevel = Literal["measured", "mixed", "estimated", "assumed", "insufficient"]
CalcStatus = Literal["computed", "insufficient_evidence", "not_applicable", "error"]
Severity = Literal["critical", "high", "medium", "low", "info"]
RuleOutcome = Literal["triggered", "not_triggered", "insufficient_evidence", "not_configured"]
CompatOutcome = Literal["compatible", "incompatible", "cannot_evaluate"]
TaskPriority = Literal["P1", "P2", "P3"]
TaskType = Literal["measurement", "experiment", "expert_review", "data_request"]


def _default_thresholds() -> Any:
    """Build the default threshold snapshot without importing readiness eagerly."""
    from scalebridge_science.readiness.thresholds import ThresholdConfig

    return ThresholdConfig()


class Quantity(BaseModel):
    """A physical quantity in internal SI units plus original provenance."""

    value: float
    unit: str
    original_value: float | None = None
    original_unit: str | None = None
    display_value: float | None = None
    display_unit: str | None = None
    provenance: Provenance = Provenance.manual_entry
    value_nature: ValueNature = ValueNature.measured
    source_ref: str | None = None
    note: str | None = None


class KlaEvidencePoint(BaseModel):
    """Documented or measured kLa point for a specific vessel and operating condition."""

    id: str
    kla: Quantity
    agitation_speed: Quantity | None = None
    gas_flow: Quantity | None = None
    working_volume: Quantity | None = None
    medium_description: str | None = None
    temperature: Quantity | None = None
    method: str | None = None


class MixingTimeEvidencePoint(BaseModel):
    """Documented or measured mixing time point for a vessel."""

    id: str
    mixing_time: Quantity
    agitation_speed: Quantity | None = None
    working_volume: Quantity | None = None
    method: str | None = None


class VesselSpec(BaseModel):
    """Immutable snapshot of a bioreactor vessel version."""

    vessel_version_id: str
    name: str
    scale_class: Literal["lab", "pilot", "production", "other"] = "lab"
    impeller_type: str | None = None
    impeller_count: int | None = None
    sparger_type: str | None = None
    instrumentation: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    parameters: dict[str, Quantity] = Field(default_factory=dict)
    kla_evidence: list[KlaEvidencePoint] = Field(default_factory=list)
    mixing_time_evidence: list[MixingTimeEvidencePoint] = Field(default_factory=list)


class ProcessSummary(BaseModel):
    """Derived operating and extreme statistics from source fermentation batches."""

    batch_ids: list[str] = Field(default_factory=list)
    aggregation_description: str = (
        "Median over selected window for operating variables; min for DO; max for OUR"
    )
    operating: dict[str, Quantity] = Field(default_factory=dict)
    extremes: dict[str, Quantity] = Field(default_factory=dict)
    calibration_status: dict[str, str] = Field(default_factory=dict)
    high_severity_dq_variables: list[str] = Field(default_factory=list)
    required_instruments: list[str] = Field(default_factory=list)
    required_controls: list[str] = Field(default_factory=list)


class MediumProperties(BaseModel):
    """Broth physical properties from Passport or Scenario assumptions."""

    name: str | None = None
    density: Quantity | None = None
    viscosity: Quantity | None = None
    oxygen_saturation_concentration: Quantity | None = None


class CriterionSelection(BaseModel):
    criterion_id: Literal["S-PV", "S-TIP", "S-KLA"]
    is_primary: bool = False


class ScenarioConfig(BaseModel):
    criteria: list[CriterionSelection]
    aeration_basis: Literal["S-VVM", "S-VS"] = "S-VVM"
    target_working_volume: Quantity
    source_kla_point_id: str | None = None
    target_kla_point_id: str | None = None
    constraints: dict[str, Quantity] = Field(default_factory=dict)
    thresholds: "ThresholdConfig" = Field(default_factory=_default_thresholds)  # noqa: UP037


class AssessmentInput(BaseModel):
    contract_version: str = "0.1.0"
    source_vessel: VesselSpec
    target_vessel: VesselSpec
    process: ProcessSummary
    medium: MediumProperties
    scenario: ScenarioConfig
    is_synthetic: bool = False


class CalculationResult(BaseModel):
    formula_id: str
    formula_name: str
    formula_version: str
    review_status: Literal["draft", "pending_review", "approved", "deprecated"]
    scale: Literal["source", "target"]
    criterion_id: str | None = None
    equation: str
    inputs: dict[str, Quantity] = Field(default_factory=dict)
    output: Quantity | None = None
    status: CalcStatus
    missing_inputs: list[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TradeOffRow(BaseModel):
    criterion_id: str
    criterion_name: str
    is_primary: bool
    status: CalcStatus
    missing_inputs: list[str] = Field(default_factory=list)
    target_operating_point: dict[str, Quantity] = Field(default_factory=dict)
    descriptors_target: dict[str, Quantity | None] = Field(default_factory=dict)
    descriptor_ratios: dict[str, float | None] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class InputRef(BaseModel):
    kind: Literal[
        "vessel_parameter",
        "measurement_summary",
        "scenario_input",
        "medium_property",
        "calculation",
        "compatibility_check",
    ]
    ref_id: str | None = None
    key: str


class CompatibilityCheck(BaseModel):
    check_id: str
    criterion_id: str | None = None
    parameter_key: str
    title: str
    required_value_si: float | None = None
    capability_min_si: float | None = None
    capability_max_si: float | None = None
    unit_si: str
    display_unit: str
    required_display: float | None = None
    capability_min_display: float | None = None
    capability_max_display: float | None = None
    outcome: CompatOutcome
    explanation: str
    input_refs: list[InputRef] = Field(default_factory=list)


class RiskFlag(BaseModel):
    rule_id: str
    rule_version: str
    category: Literal["oxygen_transfer", "mixing", "thermal", "data", "equipment"]
    severity: Severity
    outcome: RuleOutcome
    title: str
    explanation: str
    input_refs: list[InputRef] = Field(default_factory=list)
    evidence_gap: str | None = None
    threshold_used: dict[str, Any] | None = None
    validation_task_codes: list[str] = Field(default_factory=list)


class ValidationTaskSpec(BaseModel):
    task_code: str
    task_type: TaskType
    title: str
    description: str
    priority: TaskPriority
    triggered_by_rule_ids: list[str] = Field(default_factory=list)
    triggered_by_check_ids: list[str] = Field(default_factory=list)


class AssessmentSummary(BaseModel):
    overall_evidence_level: EvidenceLevel
    triggered_by_severity: dict[str, int] = Field(default_factory=dict)
    insufficient_evidence_flag_count: int = 0
    not_configured_flag_count: int = 0
    incompatible_check_count: int = 0
    cannot_evaluate_check_count: int = 0
    validation_task_count: int = 0


class AssessmentOutput(BaseModel):
    engine_version: str
    contract_version: str
    formula_registry_version: str
    rule_registry_version: str
    threshold_config_version: str
    pint_version: str
    is_synthetic: bool
    calculations: list[CalculationResult]
    trade_offs: list[TradeOffRow]
    compatibility_checks: list[CompatibilityCheck]
    risk_flags: list[RiskFlag]
    validation_tasks: list[ValidationTaskSpec]
    summary: AssessmentSummary


# ``ThresholdConfig`` lives in the readiness package.  Import it at the end so
# that contracts can be imported first without creating a circular-import
# failure; ``ScenarioConfig``'s forward reference is then resolved explicitly.
from scalebridge_science.readiness.thresholds import DescriptorBand, ThresholdConfig

if hasattr(ScenarioConfig, "model_rebuild"):
    ScenarioConfig.model_rebuild()

__all__ = [
    "AssessmentInput",
    "AssessmentOutput",
    "AssessmentSummary",
    "BaseModel",
    "CalcStatus",
    "CalculationResult",
    "CompatOutcome",
    "CompatibilityCheck",
    "CriterionSelection",
    "DescriptorBand",
    "EvidenceLevel",
    "Field",
    "InputRef",
    "KlaEvidencePoint",
    "MediumProperties",
    "MixingTimeEvidencePoint",
    "ProcessSummary",
    "Provenance",
    "Quantity",
    "RiskFlag",
    "RuleOutcome",
    "ScenarioConfig",
    "Severity",
    "TaskPriority",
    "TaskType",
    "ThresholdConfig",
    "TradeOffRow",
    "ValidationTaskSpec",
    "ValueNature",
    "VesselSpec",
]
