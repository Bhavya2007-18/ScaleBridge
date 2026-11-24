"""Versioned risk-rule registry and shared rule context (docs/12 §2, §4)."""

from __future__ import annotations

from scalebridge_science._pydantic_compat import BaseModel
from scalebridge_science.contracts import (
    AssessmentInput,
    CalculationResult,
    CompatibilityCheck,
    Severity,
    TradeOffRow,
)
from scalebridge_science.readiness.thresholds import ThresholdConfig

RULE_REGISTRY_VERSION = "0.1.0"


class RuleMetadata(BaseModel):
    rule_id: str
    version: str
    category: str
    default_severity: Severity
    title: str
    description: str


class RuleContext(BaseModel):
    """Inputs available to a pure rule function (docs/12 §2)."""

    inp: AssessmentInput
    calcs: list[CalculationResult]
    trade_offs: list[TradeOffRow]
    checks: list[CompatibilityCheck]
    thresholds: ThresholdConfig


RULE_REGISTRY: dict[str, RuleMetadata] = {
    "R-DAT-001": RuleMetadata(
        rule_id="R-DAT-001",
        version="1.0.0",
        category="data",
        default_severity="high",
        title="Required engineering inputs missing for scale-up calculation",
        description="Flags calculations or criteria that returned insufficient_evidence due to missing parameters.",
    ),
    "R-DAT-002": RuleMetadata(
        rule_id="R-DAT-002",
        version="1.0.0",
        category="data",
        default_severity="medium",
        title="Scale-up calculation relies on user-assumed properties",
        description="Flags calculations whose evidence_level is 'assumed' rather than measured.",
    ),
    "R-DAT-003": RuleMetadata(
        rule_id="R-DAT-003",
        version="1.0.0",
        category="data",
        default_severity="medium",
        title="Source batch data-quality issues affect engineering inputs",
        description="Flags source batch variables with high/critical data-quality anomalies.",
    ),
    "R-DAT-004": RuleMetadata(
        rule_id="R-DAT-004",
        version="1.0.0",
        category="data",
        default_severity="low",
        title="DO or pH sensor calibration status undocumented",
        description="Flags missing pre-run calibration records for primary chemical probes.",
    ),
    "R-DAT-005": RuleMetadata(
        rule_id="R-DAT-005",
        version="1.0.0",
        category="data",
        default_severity="info",
        title="Assessment uses synthetic or demonstration dataset",
        description="Explicitly marks synthetic/demo inputs so outputs are never mistaken for partner pilot validation.",
    ),
    "R-DAT-006": RuleMetadata(
        rule_id="R-DAT-006",
        version="1.0.0",
        category="data",
        default_severity="info",
        title="Assessment includes formulas pending domain-expert sign-off",
        description="Highlights proposed engineering correlations awaiting formal advisor review.",
    ),
    "R-OXY-001": RuleMetadata(
        rule_id="R-OXY-001",
        version="1.0.0",
        category="oxygen_transfer",
        default_severity="high",
        title="Source batch dissolved oxygen fell below required threshold",
        description="Checks whether minimum observed DO in the lab batch dropped below the required minimum DO.",
    ),
    "R-OXY-002": RuleMetadata(
        rule_id="R-OXY-002",
        version="1.0.0",
        category="oxygen_transfer",
        default_severity="high",
        title="No kLa evidence documented for target vessel",
        description="Flags missing volumetric oxygen mass-transfer coefficient evidence for the target bioreactor.",
    ),
    "R-OXY-003": RuleMetadata(
        rule_id="R-OXY-003",
        version="1.0.0",
        category="oxygen_transfer",
        default_severity="high",
        title="Target OTR capacity vs peak process oxygen demand (OUR)",
        description="Compares target OTR = kLa(C* - C_L) against peak lab oxygen uptake rate OUR.",
    ),
    "R-OXY-004": RuleMetadata(
        rule_id="R-OXY-004",
        version="1.0.0",
        category="oxygen_transfer",
        default_severity="medium",
        title="kLa evidence conditions or medium differ from evaluated process point",
        description="Flags kLa values measured at different (N, Q_g, V_w), in water vs broth, or from unvalidated correlations.",
    ),
    "R-OXY-005": RuleMetadata(
        rule_id="R-OXY-005",
        version="1.0.0",
        category="oxygen_transfer",
        default_severity="medium",
        title="No kLa evidence documented for source laboratory vessel",
        description="Flags missing baseline kLa characterization in the laboratory vessel.",
    ),
    "R-MIX-001": RuleMetadata(
        rule_id="R-MIX-001",
        version="1.0.0",
        category="mixing",
        default_severity="high",
        title="Scale-up criterion trade-off violates process constraint or ratio band",
        description="Checks non-preserved hydrodynamic descriptors against user constraints (e.g. max tip speed) or configured ratio bands.",
    ),
    "R-MIX-002": RuleMetadata(
        rule_id="R-MIX-002",
        version="1.0.0",
        category="mixing",
        default_severity="medium",
        title="Mixing-time characterization missing for target vessel",
        description="Flags absence of documented mixing-time evidence at target scale.",
    ),
    "R-MIX-003": RuleMetadata(
        rule_id="R-MIX-003",
        version="1.0.0",
        category="mixing",
        default_severity="medium",
        title="Impeller Reynolds number vs turbulent regime threshold",
        description="Checks whether Re meets the configured turbulent threshold required for constant power number N_p.",
    ),
    "R-MIX-004": RuleMetadata(
        rule_id="R-MIX-004",
        version="1.0.0",
        category="mixing",
        default_severity="medium",
        title="Geometric or impeller dissimilarity between source and target vessels",
        description="Compares impeller type, impeller count, D/T, and H_L/T between scales.",
    ),
    "R-THM-001": RuleMetadata(
        rule_id="R-THM-001",
        version="1.0.0",
        category="thermal",
        default_severity="high",
        title="Target vessel cooling capacity undocumented",
        description="Flags missing cooling capability specification on the target vessel.",
    ),
    "R-THM-002": RuleMetadata(
        rule_id="R-THM-002",
        version="1.0.0",
        category="thermal",
        default_severity="high",
        title="Estimated process heat load vs target vessel cooling capacity",
        description="Compares user-supplied heat load against target vessel cooling capability.",
    ),
    "R-THM-003": RuleMetadata(
        rule_id="R-THM-003",
        version="1.0.0",
        category="thermal",
        default_severity="low",
        title="Source batch temperature deviation from setpoint",
        description="Checks source batch temperature excursion against configured maximum deviation.",
    ),
    "R-EQP-001": RuleMetadata(
        rule_id="R-EQP-001",
        version="1.0.0",
        category="equipment",
        default_severity="critical",
        title="Required target agitation speed outside vessel operating range",
        description="Triggered when C-AGIT-RANGE is incompatible.",
    ),
    "R-EQP-002": RuleMetadata(
        rule_id="R-EQP-002",
        version="1.0.0",
        category="equipment",
        default_severity="critical",
        title="Required agitation power exceeds target vessel motor limit",
        description="Triggered when C-MOTOR-POWER is incompatible.",
    ),
    "R-EQP-003": RuleMetadata(
        rule_id="R-EQP-003",
        version="1.0.0",
        category="equipment",
        default_severity="critical",
        title="Required target gas flow outside vessel sparger flow range",
        description="Triggered when C-GAS-RANGE is incompatible.",
    ),
    "R-EQP-004": RuleMetadata(
        rule_id="R-EQP-004",
        version="1.0.0",
        category="equipment",
        default_severity="critical",
        title="Target working volume outside vessel operable volume envelope",
        description="Triggered when C-VOLUME-RANGE is incompatible.",
    ),
    "R-EQP-005": RuleMetadata(
        rule_id="R-EQP-005",
        version="1.0.0",
        category="equipment",
        default_severity="high",
        title="Required process instrumentation or control loop unavailable on target vessel",
        description="Triggered when C-INSTRUMENT is incompatible.",
    ),
    "R-EQP-006": RuleMetadata(
        rule_id="R-EQP-006",
        version="1.0.0",
        category="equipment",
        default_severity="medium",
        title="Target vessel capability envelope incomplete for compatibility check",
        description="Triggered when one or more C-* compatibility checks return cannot_evaluate.",
    ),
}


__all__ = ["RULE_REGISTRY", "RULE_REGISTRY_VERSION", "RuleContext", "RuleMetadata"]
