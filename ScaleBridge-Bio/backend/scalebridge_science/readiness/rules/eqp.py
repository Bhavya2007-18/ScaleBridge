"""Equipment risk rules (R-EQP-*) (docs/12 §4)."""

from __future__ import annotations

from scalebridge_science.contracts import InputRef, RiskFlag, Severity
from scalebridge_science.readiness.registry import RULE_REGISTRY, RuleContext

_CHECK_TO_RULE: dict[str, tuple[str, list[str]]] = {
    "C-AGIT-RANGE": ("R-EQP-001", ["VT-REVIEW-EQUIPMENT"]),
    "C-MOTOR-POWER": ("R-EQP-002", ["VT-REVIEW-EQUIPMENT", "VT-MEASURE-POWER"]),
    "C-GAS-RANGE": ("R-EQP-003", ["VT-REVIEW-EQUIPMENT"]),
    "C-VOLUME-RANGE": ("R-EQP-004", ["VT-REVIEW-EQUIPMENT"]),
    "C-INSTRUMENT": ("R-EQP-005", ["VT-REVIEW-EQUIPMENT"]),
}


def evaluate_eqp_rules(ctx: RuleContext) -> list[RiskFlag]:
    """Evaluate equipment rules against a shared rule context."""
    flags: list[RiskFlag] = []
    checks = ctx.checks
    primary_cids = {c.criterion_id for c in ctx.inp.scenario.criteria if c.is_primary}

    for chk in checks:
        mapping = _CHECK_TO_RULE.get(chk.check_id)
        if not mapping:
            continue
        rid, tcodes = mapping
        rmeta = RULE_REGISTRY[rid]
        if chk.outcome == "incompatible":
            is_prim = chk.criterion_id is None or chk.criterion_id in primary_cids
            sev: Severity = (
                "critical" if is_prim and rmeta.default_severity == "critical" else "high"
            )
            flags.append(
                RiskFlag(
                    rule_id=rid,
                    rule_version=rmeta.version,
                    category="equipment",
                    severity=sev,
                    outcome="triggered",
                    title=f"{rmeta.title}"
                    + (f" ({chk.criterion_id})" if chk.criterion_id else ""),
                    explanation=chk.explanation,
                    input_refs=chk.input_refs,
                    evidence_gap=(
                        "Adjust target operating point/volume, select an alternative criterion, or "
                        "verify if target vessel hardware can be reconfigured."
                    ),
                    validation_task_codes=tcodes,
                )
            )

    cannot_eval_checks = [c for c in checks if c.outcome == "cannot_evaluate"]
    if cannot_eval_checks:
        c_names = ", ".join(sorted({c.check_id for c in cannot_eval_checks}))
        flags.append(
            RiskFlag(
                rule_id="R-EQP-006",
                rule_version="1.0.0",
                category="equipment",
                severity="medium",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-EQP-006"].title,
                explanation=(
                    f"Equipment compatibility check(s) ({c_names}) could not be evaluated due to "
                    "missing vessel capability limits or missing operating point inputs."
                ),
                input_refs=[
                    InputRef(kind="compatibility_check", key=c.check_id)
                    for c in cannot_eval_checks
                ],
                evidence_gap=(
                    "Complete target vessel capability envelope (min/max agitation, motor power, gas "
                    "flow, cooling, instrumentation)."
                ),
                validation_task_codes=["VT-DATA-VESSEL-SPEC"],
            )
        )

    return flags


__all__ = ["evaluate_eqp_rules"]
