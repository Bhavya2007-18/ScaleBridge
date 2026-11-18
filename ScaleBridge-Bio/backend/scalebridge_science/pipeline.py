"""Top-level pure assessment execution pipeline (`run_assessment`)."""

from __future__ import annotations

from scalebridge_science import (
    CONTRACT_VERSION,
    ENGINE_VERSION,
    FORMULA_REGISTRY_VERSION,
    RULE_REGISTRY_VERSION,
)
from scalebridge_science.contracts import (
    AssessmentInput,
    AssessmentOutput,
    AssessmentSummary,
)
from scalebridge_science.criteria import evaluate_criteria_and_calculations
from scalebridge_science.evidence import derive_overall_evidence_level
from scalebridge_science.readiness import (
    evaluate_compatibility_checks,
    evaluate_risk_rules,
    generate_validation_tasks,
)
from scalebridge_science.units import PINT_VERSION


def run_assessment(inp: AssessmentInput) -> AssessmentOutput:
    """Execute a complete, deterministic scale-up assessment from `AssessmentInput`."""
    calcs, trade_offs = evaluate_criteria_and_calculations(inp)
    checks = evaluate_compatibility_checks(inp, trade_offs)
    flags = evaluate_risk_rules(inp, calcs, trade_offs, checks)
    tasks = generate_validation_tasks(flags, checks)

    overall_ev = derive_overall_evidence_level(c.evidence_level for c in calcs)
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    insuff_count = 0
    not_cfg_count = 0

    for f in flags:
        if f.outcome == "triggered":
            sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
        elif f.outcome == "insufficient_evidence":
            insuff_count += 1
        elif f.outcome == "not_configured":
            not_cfg_count += 1

    incompat_count = sum(1 for c in checks if c.outcome == "incompatible")
    cannot_eval_count = sum(1 for c in checks if c.outcome == "cannot_evaluate")

    summary = AssessmentSummary(
        overall_evidence_level=overall_ev,
        triggered_by_severity=sev_counts,
        insufficient_evidence_flag_count=insuff_count,
        not_configured_flag_count=not_cfg_count,
        incompatible_check_count=incompat_count,
        cannot_evaluate_check_count=cannot_eval_count,
        validation_task_count=len(tasks),
    )

    return AssessmentOutput(
        engine_version=ENGINE_VERSION,
        contract_version=CONTRACT_VERSION,
        formula_registry_version=FORMULA_REGISTRY_VERSION,
        rule_registry_version=RULE_REGISTRY_VERSION,
        threshold_config_version=inp.scenario.thresholds.version,
        pint_version=PINT_VERSION,
        is_synthetic=inp.is_synthetic,
        calculations=calcs,
        trade_offs=trade_offs,
        compatibility_checks=checks,
        risk_flags=flags,
        validation_tasks=tasks,
        summary=summary,
    )
