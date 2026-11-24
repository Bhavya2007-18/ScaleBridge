"""Oxygen-transfer risk rules (R-OXY-*) (docs/12 §4)."""

from __future__ import annotations

from scalebridge_science.contracts import InputRef, RiskFlag
from scalebridge_science.criteria import check_kla_mismatch_warnings, find_kla_point
from scalebridge_science.readiness.registry import RULE_REGISTRY, RuleContext
from scalebridge_science.units import convert_value


def evaluate_oxy_rules(ctx: RuleContext) -> list[RiskFlag]:
    """Evaluate oxygen-transfer rules against a shared rule context."""
    flags: list[RiskFlag] = []
    inp = ctx.inp
    calcs = ctx.calcs
    trade_offs = ctx.trade_offs
    thresh = ctx.thresholds

    src = inp.source_vessel
    tgt = inp.target_vessel
    proc = inp.process
    scen = inp.scenario

    # --- R-OXY-001: Source DO minimum ---
    do_min = proc.extremes.get("do_min")
    do_req = scen.constraints.get("min_do_required")
    do_thresh_val = do_req.value if do_req is not None else thresh.do_critical_percent
    if do_min is None:
        flags.append(
            RiskFlag(
                rule_id="R-OXY-001",
                rule_version="1.0.0",
                category="oxygen_transfer",
                severity="high",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-OXY-001"].title,
                explanation="Source batch dissolved oxygen minimum (`do_min`) is unavailable.",
                input_refs=[InputRef(kind="measurement_summary", key="do_min")],
                evidence_gap=(
                    "Provide dissolved oxygen time-series data from laboratory fermentation runs."
                ),
                validation_task_codes=["VT-EXP-DO-PROFILE"],
            )
        )
    elif do_thresh_val is None:
        flags.append(
            RiskFlag(
                rule_id="R-OXY-001",
                rule_version="1.0.0",
                category="oxygen_transfer",
                severity="low",
                outcome="not_configured",
                title=RULE_REGISTRY["R-OXY-001"].title,
                explanation=(
                    f"Minimum observed source DO was {do_min.value:.1f} % air sat, but neither "
                    "scenario constraint 'min_do_required' nor threshold 'do_critical_percent' is "
                    "configured."
                ),
                input_refs=[InputRef(kind="measurement_summary", key="do_min")],
                threshold_used={"do_critical_percent": None},
            )
        )
    elif do_min.value < do_thresh_val:
        flags.append(
            RiskFlag(
                rule_id="R-OXY-001",
                rule_version="1.0.0",
                category="oxygen_transfer",
                severity="high",
                outcome="triggered",
                title=RULE_REGISTRY["R-OXY-001"].title,
                explanation=(
                    f"Source batch minimum DO reached {do_min.value:.1f} % air sat, falling below "
                    f"required minimum DO ({do_thresh_val:.1f} % air sat). The lab process may "
                    "already experience oxygen limitation."
                ),
                input_refs=[
                    InputRef(kind="measurement_summary", key="do_min"),
                    InputRef(kind="scenario_input", key="min_do_required"),
                ],
                evidence_gap=(
                    "Investigate whether transient DO dips at bench scale impacted yield and confirm "
                    "critical DO threshold."
                ),
                threshold_used={"min_do_required_pct": do_thresh_val},
                validation_task_codes=["VT-EXP-DO-PROFILE", "VT-REVIEW-OXY"],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-OXY-001",
                rule_version="1.0.0",
                category="oxygen_transfer",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-OXY-001"].title,
                explanation=(
                    f"Source batch minimum DO ({do_min.value:.1f} % air sat) remained at or above "
                    f"required threshold ({do_thresh_val:.1f} % air sat)."
                ),
                input_refs=[InputRef(kind="measurement_summary", key="do_min")],
                threshold_used={"min_do_required_pct": do_thresh_val},
            )
        )

    # --- R-OXY-002 & R-OXY-005: Target & Source kLa evidence presence ---
    tgt_kla = find_kla_point(tgt.kla_evidence, scen.target_kla_point_id)
    src_kla = find_kla_point(src.kla_evidence, scen.source_kla_point_id)

    if tgt_kla is None:
        flags.append(
            RiskFlag(
                rule_id="R-OXY-002",
                rule_version="1.0.0",
                category="oxygen_transfer",
                severity="high",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-OXY-002"].title,
                explanation=(
                    "Target vessel profile has no documented kLa evidence point. Target oxygen "
                    "transfer rate (OTR) cannot be evaluated."
                ),
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="kla_evidence",
                    )
                ],
                evidence_gap=(
                    "Measured kLa in target vessel across planned agitation and aeration operating "
                    "envelope."
                ),
                validation_task_codes=["VT-KLA-TARGET"],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-OXY-002",
                rule_version="1.0.0",
                category="oxygen_transfer",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-OXY-002"].title,
                explanation=(
                    f"Target vessel kLa evidence point '{tgt_kla.id}' "
                    f"({tgt_kla.kla.display_value or tgt_kla.kla.value:.1f} "
                    f"{tgt_kla.kla.display_unit or tgt_kla.kla.unit}) is available."
                ),
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key=f"kla_evidence:{tgt_kla.id}",
                    )
                ],
            )
        )

    if src_kla is None:
        flags.append(
            RiskFlag(
                rule_id="R-OXY-005",
                rule_version="1.0.0",
                category="oxygen_transfer",
                severity="medium",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-OXY-005"].title,
                explanation="Source laboratory vessel has no documented kLa evidence point.",
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=src.vessel_version_id,
                        key="kla_evidence",
                    )
                ],
                evidence_gap=(
                    "Characterize baseline kLa in the source laboratory vessel at reference "
                    "operating conditions."
                ),
                validation_task_codes=["VT-KLA-SOURCE"],
            )
        )

    # --- R-OXY-003: Target OTR vs Peak OUR ---
    our_max = proc.extremes.get("our_max")
    otr_targets = [
        c
        for c in calcs
        if c.formula_id == "F-OTR-001"
        and c.scale == "target"
        and c.status == "computed"
        and c.output is not None
    ]
    if our_max is None or not otr_targets:
        missing_oxy: list[str] = []
        if our_max is None:
            missing_oxy.append("peak oxygen uptake rate (OUR_max)")
        if not otr_targets:
            missing_oxy.append("target OTR (requires target kLa, C*, and required DO)")
        flags.append(
            RiskFlag(
                rule_id="R-OXY-003",
                rule_version="1.0.0",
                category="oxygen_transfer",
                severity="high",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-OXY-003"].title,
                explanation=(
                    "Cannot compare target oxygen transfer capacity against process oxygen demand: "
                    f"missing {', '.join(missing_oxy)}."
                ),
                input_refs=[
                    InputRef(kind="measurement_summary", key="our_max"),
                    InputRef(kind="calculation", key="F-OTR-001:target"),
                ],
                evidence_gap=(
                    f"Quantify {', '.join(missing_oxy)} to verify oxygen transfer adequacy before "
                    "pilot scale-up."
                ),
                validation_task_codes=["VT-KLA-TARGET", "VT-MEASURE-OUR", "VT-REVIEW-OXY"],
            )
        )
    else:
        margin = thresh.otr_demand_margin or 0.0
        required_otr_si = our_max.value * (1.0 + margin)
        our_disp = our_max.display_value or convert_value(
            our_max.value, "mol / (m**3 * second)", "mmol/(L*h)"
        )
        req_disp = convert_value(required_otr_si, "mol / (m**3 * second)", "mmol/(L*h)")
        failing = [
            c for c in otr_targets if c.output is not None and c.output.value < required_otr_si
        ]
        if failing:
            c0 = failing[0]
            assert c0.output is not None
            otr_disp = c0.output.display_value or convert_value(
                c0.output.value, "mol / (m**3 * second)", "mmol/(L*h)"
            )
            flags.append(
                RiskFlag(
                    rule_id="R-OXY-003",
                    rule_version="1.0.0",
                    category="oxygen_transfer",
                    severity="high",
                    outcome="triggered",
                    title=RULE_REGISTRY["R-OXY-003"].title,
                    explanation=(
                        f"Target OTR at required DO ({otr_disp:.2f} mmol/(L·h)) is below required "
                        f"oxygen demand ({req_disp:.2f} mmol/(L·h), based on peak OUR "
                        f"{our_disp:.2f} mmol/(L·h) and margin {margin * 100:.0f}%)."
                    ),
                    input_refs=[
                        InputRef(kind="calculation", key=f"F-OTR-001:target:{c0.criterion_id}"),
                        InputRef(kind="measurement_summary", key="our_max"),
                    ],
                    evidence_gap=(
                        "Verify target kLa at higher agitation/aeration or evaluate oxygen enrichment "
                        "/ headpressure strategy with a bioprocess engineer."
                    ),
                    threshold_used={"otr_demand_margin": thresh.otr_demand_margin},
                    validation_task_codes=["VT-KLA-TARGET", "VT-REVIEW-OXY"],
                )
            )
        else:
            c0 = otr_targets[0]
            assert c0.output is not None
            otr_disp = c0.output.display_value or convert_value(
                c0.output.value, "mol / (m**3 * second)", "mmol/(L*h)"
            )
            flags.append(
                RiskFlag(
                    rule_id="R-OXY-003",
                    rule_version="1.0.0",
                    category="oxygen_transfer",
                    severity="info",
                    outcome="not_triggered",
                    title=RULE_REGISTRY["R-OXY-003"].title,
                    explanation=(
                        f"Evaluated target OTR ({otr_disp:.2f} mmol/(L·h)) meets or exceeds peak "
                        f"oxygen demand ({req_disp:.2f} mmol/(L·h))."
                    ),
                    input_refs=[
                        InputRef(kind="calculation", key=f"F-OTR-001:target:{c0.criterion_id}"),
                        InputRef(kind="measurement_summary", key="our_max"),
                    ],
                    threshold_used={"otr_demand_margin": thresh.otr_demand_margin},
                )
            )

    # --- R-OXY-004: kLa representativeness ---
    if tgt_kla is not None:
        mismatch_reasons: list[str] = []
        for row in trade_offs:
            w = check_kla_mismatch_warnings(
                tgt_kla,
                row.target_operating_point.get("N"),
                row.target_operating_point.get("Q_g"),
                row.target_operating_point.get("V_w"),
            )
            mismatch_reasons.extend(w)
        if tgt_kla.kla.provenance in ("published_correlation", "user_assumption"):
            mismatch_reasons.append(
                f"Target kLa provenance is '{tgt_kla.kla.provenance}' rather than a physical "
                "measurement in the target vessel."
            )
        if tgt_kla.medium_description and "water" in tgt_kla.medium_description.lower():
            mismatch_reasons.append(
                f"Target kLa was characterized in '{tgt_kla.medium_description}', which may differ "
                "from coalescing/non-coalescing fermentation broth."
            )
        if mismatch_reasons:
            flags.append(
                RiskFlag(
                    rule_id="R-OXY-004",
                    rule_version="1.0.0",
                    category="oxygen_transfer",
                    severity="medium",
                    outcome="triggered",
                    title=RULE_REGISTRY["R-OXY-004"].title,
                    explanation=" ".join(dict.fromkeys(mismatch_reasons)),
                    input_refs=[
                        InputRef(
                            kind="vessel_parameter",
                            ref_id=tgt.vessel_version_id,
                            key=f"kla_evidence:{tgt_kla.id}",
                        )
                    ],
                    evidence_gap=(
                        "Validate kLa in the target vessel at the planned (N, Q_g, V_w) operating "
                        "point and account for medium effects."
                    ),
                    validation_task_codes=["VT-KLA-TARGET", "VT-REVIEW-OXY"],
                )
            )

    return flags


__all__ = ["evaluate_oxy_rules"]
