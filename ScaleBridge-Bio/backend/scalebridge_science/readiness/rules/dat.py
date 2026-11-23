"""Data-quality risk rules (R-DAT-*) (docs/12 §4)."""

from __future__ import annotations

from scalebridge_science.contracts import InputRef, RiskFlag
from scalebridge_science.readiness.registry import RULE_REGISTRY, RuleContext


def evaluate_dat_rules(ctx: RuleContext) -> list[RiskFlag]:
    """Evaluate data-quality rules against a shared rule context."""
    flags: list[RiskFlag] = []
    inp = ctx.inp
    proc = inp.process
    calcs = ctx.calcs

    # --- R-DAT-001: Missing inputs ---
    missing_calcs = [c for c in calcs if c.status == "insufficient_evidence"]
    if missing_calcs:
        all_missing = sorted({m for c in missing_calcs for m in c.missing_inputs})
        formula_ids = sorted({c.formula_id for c in missing_calcs})
        flags.append(
            RiskFlag(
                rule_id="R-DAT-001",
                rule_version="1.0.0",
                category="data",
                severity="high",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-DAT-001"].title,
                explanation=(
                    f"{len(missing_calcs)} calculation(s) ({', '.join(formula_ids)}) could not "
                    f"be evaluated due to missing inputs: {', '.join(all_missing)}."
                ),
                input_refs=[
                    InputRef(
                        kind="calculation",
                        key=f"{c.formula_id}:{c.scale}:{c.criterion_id or 'baseline'}",
                    )
                    for c in missing_calcs
                ],
                evidence_gap=f"Provide measured or documented values for: {', '.join(all_missing)}",
                validation_task_codes=["VT-DATA-VESSEL-SPEC", "VT-MEASURE-VISCOSITY"],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-001",
                rule_version="1.0.0",
                category="data",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-DAT-001"].title,
                explanation="All scheduled engineering calculations had sufficient input parameters to execute.",
                input_refs=[InputRef(kind="scenario_input", key="all_inputs")],
            )
        )

    # --- R-DAT-002: Assumed inputs ---
    assumed_calcs = [
        c for c in calcs if c.status == "computed" and c.evidence_level == "assumed"
    ]
    if assumed_calcs:
        fids = sorted({c.formula_id for c in assumed_calcs})
        flags.append(
            RiskFlag(
                rule_id="R-DAT-002",
                rule_version="1.0.0",
                category="data",
                severity="medium",
                outcome="triggered",
                title=RULE_REGISTRY["R-DAT-002"].title,
                explanation=(
                    f"Calculations ({', '.join(fids)}) rely on one or more user-assumed physical "
                    "properties rather than direct measurements."
                ),
                input_refs=[
                    InputRef(kind="calculation", key=f"{c.formula_id}:{c.scale}")
                    for c in assumed_calcs[:6]
                ],
                evidence_gap=(
                    "Replace user-assumed medium/process properties (e.g. density, viscosity, C*) "
                    "with laboratory measurements."
                ),
                validation_task_codes=["VT-MEASURE-VISCOSITY"],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-002",
                rule_version="1.0.0",
                category="data",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-DAT-002"].title,
                explanation="No computed results depend on unverified user assumptions.",
                input_refs=[InputRef(kind="scenario_input", key="assumptions")],
            )
        )

    # --- R-DAT-003: Source batch DQ issues ---
    if proc.high_severity_dq_variables:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-003",
                rule_version="1.0.0",
                category="data",
                severity="medium",
                outcome="triggered",
                title=RULE_REGISTRY["R-DAT-003"].title,
                explanation=(
                    "Source batch data-quality checks flagged high/critical issues on: "
                    f"{', '.join(proc.high_severity_dq_variables)}."
                ),
                input_refs=[
                    InputRef(kind="measurement_summary", key=v)
                    for v in proc.high_severity_dq_variables
                ],
                evidence_gap=(
                    "Inspect source batch timestamp gaps, out-of-range spikes, or invalid sensor "
                    "points before relying on summary statistics."
                ),
                validation_task_codes=["VT-DATA-QUALITY"],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-003",
                rule_version="1.0.0",
                category="data",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-DAT-003"].title,
                explanation="No high-severity data-quality issues reported on source batch operating variables.",
                input_refs=[InputRef(kind="measurement_summary", key="data_quality")],
            )
        )

    # --- R-DAT-004: Calibration status ---
    uncal = [
        k
        for k, status in proc.calibration_status.items()
        if status in ("unknown", "not_calibrated")
    ]
    if uncal:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-004",
                rule_version="1.0.0",
                category="data",
                severity="low",
                outcome="triggered",
                title=RULE_REGISTRY["R-DAT-004"].title,
                explanation=(
                    "Calibration status is '"
                    + ", ".join(f"{k}:{proc.calibration_status[k]}" for k in uncal)
                    + "'."
                ),
                input_refs=[InputRef(kind="measurement_summary", key=k) for k in uncal],
                evidence_gap="Document pre-run DO and pH probe calibration certificates/logs.",
                validation_task_codes=["VT-DATA-CALIBRATION"],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-004",
                rule_version="1.0.0",
                category="data",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-DAT-004"].title,
                explanation="Primary sensor calibration status is documented as calibrated pre-run.",
                input_refs=[InputRef(kind="measurement_summary", key="calibration_status")],
            )
        )

    # --- R-DAT-005: Synthetic data ---
    if inp.is_synthetic:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-005",
                rule_version="1.0.0",
                category="data",
                severity="info",
                outcome="triggered",
                title=RULE_REGISTRY["R-DAT-005"].title,
                explanation=(
                    "This assessment uses data marked as synthetic/demonstration. Outputs illustrate "
                    "workflow mechanics and must not be used for physical pilot execution."
                ),
                input_refs=[InputRef(kind="scenario_input", key="is_synthetic")],
                evidence_gap=(
                    "Import a verified laboratory fermentation dataset from the actual organism and "
                    "bench bioreactor."
                ),
                validation_task_codes=["VT-DATA-REAL"],
            )
        )

    # --- R-DAT-006: Pending review formulas ---
    pending_fids = sorted(
        {
            c.formula_id
            for c in calcs
            if c.review_status == "pending_review" and c.status == "computed"
        }
    )
    if pending_fids:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-006",
                rule_version="1.0.0",
                category="data",
                severity="info",
                outcome="triggered",
                title=RULE_REGISTRY["R-DAT-006"].title,
                explanation=(
                    "Computed results include formula(s) with status 'pending_review': "
                    f"{', '.join(pending_fids)}."
                ),
                input_refs=[InputRef(kind="calculation", key=fid) for fid in pending_fids],
                evidence_gap=(
                    "Complete independent bioprocess advisor review of proposed engineering "
                    "correlations."
                ),
                validation_task_codes=["VT-REVIEW-FORMULAS"],
            )
        )

    return flags


__all__ = ["evaluate_dat_rules"]
