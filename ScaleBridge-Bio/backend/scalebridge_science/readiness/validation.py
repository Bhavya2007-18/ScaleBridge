"""Gap-to-validation-task templates (VT-*) (docs/14)."""

from __future__ import annotations

from typing import cast

from scalebridge_science.contracts import (
    CompatibilityCheck,
    RiskFlag,
    TaskPriority,
    TaskType,
    ValidationTaskSpec,
)

VALIDATION_TASK_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "VT-KLA-TARGET": (
        "measurement",
        "P1",
        "Measure or obtain verified kLa in target vessel across planned (N, Q_g) range",
        "Conduct dynamic gassing-out or sulfite kLa characterization in the target vessel "
        "(or obtain verified facility test data) covering the target agitation and aeration "
        "operating point.",
    ),
    "VT-KLA-SOURCE": (
        "measurement",
        "P2",
        "Measure kLa in source laboratory vessel at reference operating point",
        "Determine baseline kLa in the laboratory vessel at the process agitation and airflow "
        "setpoints to anchor oxygen transfer comparisons.",
    ),
    "VT-MEASURE-OUR": (
        "measurement",
        "P1",
        "Quantify peak oxygen uptake rate (OUR) in laboratory process",
        "Measure peak OUR via exhaust gas O₂/CO₂ analysis or dynamic DO depletion during peak "
        "metabolic phase.",
    ),
    "VT-EXP-DO-PROFILE": (
        "experiment",
        "P2",
        "Verify DO sensitivity and minimum acceptable DO in bench-scale run",
        "Review bench-scale DO profiles and determine critical DO threshold below which "
        "specific productivity or viability degrades.",
    ),
    "VT-REVIEW-OXY": (
        "expert_review",
        "P1",
        "Bioprocess engineer review of oxygen transfer balance and gas supply strategy",
        "Review OTR = kLa(C* - C_L) driving force, headpressure effects, and O₂ enrichment "
        "options with a senior bioprocess engineer.",
    ),
    "VT-REVIEW-CRITERIA": (
        "expert_review",
        "P1",
        "Bioprocess engineer review of scale-up criterion selection and descriptor trade-offs",
        "Evaluate trade-offs between preserving constant P/V, tip speed, and vvm/v_s for the "
        "organism's shear and oxygen sensitivity.",
    ),
    "VT-MEASURE-MIXING": (
        "measurement",
        "P2",
        "Characterize mixing time in target vessel (or review existing facility mixing study)",
        "Obtain or perform a tracer mixing-time (t_95) study in the target vessel at planned "
        "agitation speed to assess substrate/pH gradient risk.",
    ),
    "VT-MEASURE-VISCOSITY": (
        "measurement",
        "P2",
        "Measure broth density and dynamic viscosity at process conditions",
        "Measure end-of-batch broth density and viscosity (and shear-rate dependence if "
        "non-Newtonian) to replace assumed medium properties.",
    ),
    "VT-REVIEW-GEOMETRY": (
        "expert_review",
        "P2",
        "Review geometric and impeller differences between source and target vessels",
        "Assess hydrodynamic impact of differences in impeller type, impeller count, D/T, and "
        "H_L/T aspect ratio.",
    ),
    "VT-REVIEW-FORMULAS": (
        "expert_review",
        "P2",
        "Domain-expert sign-off on pending-review formulas and power-number assumptions",
        "Have the bioprocess scientific lead and advisor review ungassed power number N_p and "
        "pending engineering correlations.",
    ),
    "VT-DATA-COOLING": (
        "data_request",
        "P1",
        "Request target vessel cooling capacity specification from facility/vendor",
        "Obtain maximum jacket/coil heat removal rate (kW) at the target fermentation "
        "temperature and utility chilled-water supply temperature.",
    ),
    "VT-REVIEW-THERMAL": (
        "expert_review",
        "P1",
        "Perform metabolic + agitation heat balance against target cooling capability",
        "Calculate peak metabolic heat generation (from OUR or sugar consumption) plus "
        "mechanical agitation power against target cooling capacity.",
    ),
    "VT-REVIEW-EQUIPMENT": (
        "expert_review",
        "P1",
        "Resolve target vessel capability incompatibility",
        "Target operating point exceeds documented vessel limits; adjust working volume, "
        "modify scale-up criterion, or evaluate an alternative vessel.",
    ),
    "VT-DATA-VESSEL-SPEC": (
        "data_request",
        "P2",
        "Obtain missing vessel geometry and capability specifications",
        "Complete missing vessel profile fields from vendor engineering drawings or facility "
        "P&ID / datasheets.",
    ),
    "VT-MEASURE-POWER": (
        "measurement",
        "P2",
        "Verify target motor/drive power limit and impeller power number N_p",
        "Confirm available shaft power after drivetrain losses and gassed power draw reduction.",
    ),
    "VT-DATA-QUALITY": (
        "data_request",
        "P2",
        "Resolve source batch data-quality issues",
        "Inspect and document timestamp gaps, duplicate points, or out-of-range sensor "
        "readings in source batch exports.",
    ),
    "VT-DATA-CALIBRATION": (
        "data_request",
        "P3",
        "Document pre-run DO and pH probe calibration records",
        "Attach calibration logs confirming two-point pH and zero/100% DO calibration prior "
        "to inoculation.",
    ),
    "VT-DATA-REAL": (
        "experiment",
        "P1",
        "Replace synthetic/demo dataset with real laboratory fermentation batch data",
        "Import verified experimental batch exports from the laboratory bioreactor before "
        "making pilot transfer decisions.",
    ),
}


_PRIORITY_RANK = {"P1": 1, "P2": 2, "P3": 3}


def generate_validation_tasks(
    flags: list[RiskFlag],
    checks: list[CompatibilityCheck],
) -> list[ValidationTaskSpec]:
    by_code: dict[str, ValidationTaskSpec] = {}

    for flag in flags:
        if flag.outcome == "not_triggered":
            continue
        for code in flag.validation_task_codes:
            tmpl = VALIDATION_TASK_TEMPLATES.get(code)
            if not tmpl:
                continue
            ttype, default_prio, title, desc = tmpl
            # Escalate priority if flag is critical
            prio = "P1" if flag.severity == "critical" else default_prio
            if code not in by_code:
                by_code[code] = ValidationTaskSpec(
                    task_code=code,
                    task_type=cast(TaskType, ttype),
                    title=title,
                    description=desc,
                    priority=cast(TaskPriority, prio),
                    triggered_by_rule_ids=[flag.rule_id],
                    triggered_by_check_ids=[],
                )
            else:
                existing = by_code[code]
                if flag.rule_id not in existing.triggered_by_rule_ids:
                    existing.triggered_by_rule_ids.append(flag.rule_id)
                if _PRIORITY_RANK[prio] < _PRIORITY_RANK[existing.priority]:
                    existing.priority = cast(TaskPriority, prio)

    for chk in checks:
        if chk.outcome == "compatible":
            continue
        code = "VT-REVIEW-EQUIPMENT" if chk.outcome == "incompatible" else "VT-DATA-VESSEL-SPEC"
        if code in by_code and chk.check_id not in by_code[code].triggered_by_check_ids:
            by_code[code].triggered_by_check_ids.append(chk.check_id)

    return sorted(by_code.values(), key=lambda t: (_PRIORITY_RANK[t.priority], t.task_code))


__all__ = ["VALIDATION_TASK_TEMPLATES", "generate_validation_tasks"]
