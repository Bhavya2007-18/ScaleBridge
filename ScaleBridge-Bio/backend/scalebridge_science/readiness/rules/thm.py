"""Thermal risk rules (R-THM-*) (docs/12 §4)."""

from __future__ import annotations

from scalebridge_science.contracts import InputRef, RiskFlag
from scalebridge_science.readiness.registry import RULE_REGISTRY, RuleContext
from scalebridge_science.readiness.thresholds import ThresholdConfig


def _temperature_deviation_max(thresh: ThresholdConfig) -> float | None:
    if thresh.temperature_deviation_max is not None:
        return thresh.temperature_deviation_max
    return thresh.temperature_deviation_max_k


def evaluate_thm_rules(ctx: RuleContext) -> list[RiskFlag]:
    """Evaluate thermal rules against a shared rule context."""
    flags: list[RiskFlag] = []
    inp = ctx.inp
    tgt = inp.target_vessel
    proc = inp.process
    scen = inp.scenario
    thresh = ctx.thresholds

    # --- R-THM-001 & R-THM-002: Thermal capability ---
    q_cool = tgt.parameters.get("cooling_capacity")
    q_heat = scen.constraints.get("estimated_heat_load")
    if q_cool is None:
        flags.append(
            RiskFlag(
                rule_id="R-THM-001",
                rule_version="1.0.0",
                category="thermal",
                severity="high",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-THM-001"].title,
                explanation=(
                    "Target vessel cooling capacity is not documented. Heat removal often becomes "
                    "limiting at larger scale due to lower surface-area-to-volume ratio."
                ),
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="cooling_capacity",
                    )
                ],
                evidence_gap=(
                    "Obtain target jacket/coil cooling capacity (in W or kW at process temperature) "
                    "from facility or vendor."
                ),
                validation_task_codes=["VT-DATA-COOLING", "VT-REVIEW-THERMAL"],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-THM-001",
                rule_version="1.0.0",
                category="thermal",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-THM-001"].title,
                explanation=(
                    "Target vessel cooling capacity is documented "
                    f"({q_cool.display_value or q_cool.value:.1f} "
                    f"{q_cool.display_unit or q_cool.unit})."
                ),
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="cooling_capacity",
                    )
                ],
            )
        )

    if q_cool is not None and q_heat is not None:
        c_margin = thresh.cooling_margin or 0.0
        req_cool = q_heat.value * (1.0 + c_margin)
        if req_cool > q_cool.value:
            flags.append(
                RiskFlag(
                    rule_id="R-THM-002",
                    rule_version="1.0.0",
                    category="thermal",
                    severity="high",
                    outcome="triggered",
                    title=RULE_REGISTRY["R-THM-002"].title,
                    explanation=(
                        f"Estimated heat load with margin ({req_cool:.0f} W) exceeds target cooling "
                        f"capacity ({q_cool.value:.0f} W)."
                    ),
                    input_refs=[
                        InputRef(kind="scenario_input", key="estimated_heat_load"),
                        InputRef(
                            kind="vessel_parameter",
                            ref_id=tgt.vessel_version_id,
                            key="cooling_capacity",
                        ),
                    ],
                    evidence_gap=(
                        "Perform detailed metabolic + agitation heat balance and review cooling "
                        "utility supply temperature."
                    ),
                    threshold_used={"cooling_margin": thresh.cooling_margin},
                    validation_task_codes=["VT-REVIEW-THERMAL"],
                )
            )
        else:
            flags.append(
                RiskFlag(
                    rule_id="R-THM-002",
                    rule_version="1.0.0",
                    category="thermal",
                    severity="info",
                    outcome="not_triggered",
                    title=RULE_REGISTRY["R-THM-002"].title,
                    explanation=(
                        f"Target cooling capacity ({q_cool.value:.0f} W) exceeds estimated heat load "
                        f"({req_cool:.0f} W)."
                    ),
                    input_refs=[
                        InputRef(kind="scenario_input", key="estimated_heat_load"),
                        InputRef(
                            kind="vessel_parameter",
                            ref_id=tgt.vessel_version_id,
                            key="cooling_capacity",
                        ),
                    ],
                )
            )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-THM-002",
                rule_version="1.0.0",
                category="thermal",
                severity="medium",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-THM-002"].title,
                explanation=(
                    "Cannot evaluate thermal balance because estimated heat load or target cooling "
                    "capacity is not provided."
                ),
                input_refs=[InputRef(kind="scenario_input", key="estimated_heat_load")],
                evidence_gap=(
                    "Provide estimated peak metabolic + mechanical heat load and target cooling "
                    "capacity."
                ),
                validation_task_codes=["VT-REVIEW-THERMAL", "VT-DATA-COOLING"],
            )
        )

    # --- R-THM-003: Source batch temperature deviation ---
    t_meas = proc.operating.get("temperature")
    t_set = proc.operating.get("temperature_setpoint") or scen.constraints.get(
        "temperature_setpoint"
    )
    max_dev = _temperature_deviation_max(thresh)
    if t_meas is None or t_set is None:
        flags.append(
            RiskFlag(
                rule_id="R-THM-003",
                rule_version="1.0.0",
                category="thermal",
                severity="low",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-THM-003"].title,
                explanation=(
                    "Cannot evaluate source batch temperature deviation because measured "
                    "temperature or temperature setpoint is unavailable."
                ),
                input_refs=[InputRef(kind="measurement_summary", key="temperature")],
                evidence_gap="Provide source batch temperature time series and the process temperature setpoint.",
                validation_task_codes=["VT-REVIEW-THERMAL"],
            )
        )
    elif max_dev is None:
        flags.append(
            RiskFlag(
                rule_id="R-THM-003",
                rule_version="1.0.0",
                category="thermal",
                severity="low",
                outcome="not_configured",
                title=RULE_REGISTRY["R-THM-003"].title,
                explanation=(
                    "Source batch temperature is available, but "
                    "'temperature_deviation_max' threshold is not configured."
                ),
                input_refs=[InputRef(kind="measurement_summary", key="temperature")],
                threshold_used={"temperature_deviation_max": None},
            )
        )
    else:
        deviation = abs(t_meas.value - t_set.value)
        if deviation > max_dev:
            flags.append(
                RiskFlag(
                    rule_id="R-THM-003",
                    rule_version="1.0.0",
                    category="thermal",
                    severity="low",
                    outcome="triggered",
                    title=RULE_REGISTRY["R-THM-003"].title,
                    explanation=(
                        f"Source batch temperature deviation ({deviation:.2f} K) exceeds configured "
                        f"maximum ({max_dev:.2f} K)."
                    ),
                    input_refs=[
                        InputRef(kind="measurement_summary", key="temperature"),
                        InputRef(kind="scenario_input", key="temperature_setpoint"),
                    ],
                    evidence_gap=(
                        "Review source batch temperature control performance and assess whether "
                        "excursions affected process outcomes."
                    ),
                    threshold_used={"temperature_deviation_max": max_dev},
                    validation_task_codes=["VT-REVIEW-THERMAL"],
                )
            )
        else:
            flags.append(
                RiskFlag(
                    rule_id="R-THM-003",
                    rule_version="1.0.0",
                    category="thermal",
                    severity="info",
                    outcome="not_triggered",
                    title=RULE_REGISTRY["R-THM-003"].title,
                    explanation=(
                        f"Source batch temperature deviation ({deviation:.2f} K) is within the "
                        f"configured maximum ({max_dev:.2f} K)."
                    ),
                    input_refs=[
                        InputRef(kind="measurement_summary", key="temperature"),
                        InputRef(kind="scenario_input", key="temperature_setpoint"),
                    ],
                    threshold_used={"temperature_deviation_max": max_dev},
                )
            )

    return flags


__all__ = ["evaluate_thm_rules"]
