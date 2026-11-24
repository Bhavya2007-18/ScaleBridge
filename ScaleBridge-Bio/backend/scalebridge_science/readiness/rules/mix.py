"""Mixing and hydrodynamic risk rules (R-MIX-*) (docs/12 §4)."""

from __future__ import annotations

from scalebridge_science.contracts import InputRef, RiskFlag
from scalebridge_science.readiness.registry import RULE_REGISTRY, RuleContext
from scalebridge_science.readiness.thresholds import DescriptorBand, ThresholdConfig

#: Doc 12 uses lowercase descriptor keys; earlier snapshots used the descriptor
#: names produced by the trade-off engine.  Accept both spellings.
_BAND_ALIASES: dict[str, str] = {
    "P_per_V": "p_per_v",
    "u_tip": "u_tip",
    "Re": "re",
    "vvm": "vvm",
    "v_s": "v_s",
}


def _lookup_band(thresh: ThresholdConfig, desc_key: str) -> DescriptorBand | None:
    band = thresh.descriptor_ratio_band.get(desc_key)
    if band is None:
        band = thresh.descriptor_ratio_band.get(desc_key.lower())
    if band is None:
        alias = _BAND_ALIASES.get(desc_key)
        if alias is not None:
            band = thresh.descriptor_ratio_band.get(alias)
    return band


def _d_over_t_tolerance(thresh: ThresholdConfig) -> float | None:
    nested = thresh.geometric_similarity_tolerance
    if nested is not None and nested.d_over_t is not None:
        return nested.d_over_t
    return thresh.d_over_t_rel_tol


def _hl_over_t_tolerance(thresh: ThresholdConfig) -> float | None:
    nested = thresh.geometric_similarity_tolerance
    if nested is not None and nested.hl_over_t is not None:
        return nested.hl_over_t
    return thresh.hl_over_t_rel_tol


def evaluate_mix_rules(ctx: RuleContext) -> list[RiskFlag]:
    """Evaluate mixing rules against a shared rule context."""
    flags: list[RiskFlag] = []
    inp = ctx.inp
    calcs = ctx.calcs
    trade_offs = ctx.trade_offs
    thresh = ctx.thresholds

    src = inp.source_vessel
    tgt = inp.target_vessel
    scen = inp.scenario

    # --- R-MIX-001: Criterion trade-offs & user constraints ---
    max_tip_c = scen.constraints.get("max_tip_speed")
    max_pv_c = scen.constraints.get("max_p_per_v")
    max_vvm_c = scen.constraints.get("max_vvm")

    constraint_violations: list[str] = []
    for row in trade_offs:
        u_tip_q = row.descriptors_target.get("u_tip")
        pv_q = row.descriptors_target.get("P_per_V")
        vvm_q = row.descriptors_target.get("vvm")
        if max_tip_c is not None and u_tip_q is not None and u_tip_q.value > max_tip_c.value:
            constraint_violations.append(
                f"Criterion {row.criterion_id} yields u_tip = "
                f"{u_tip_q.display_value or u_tip_q.value:.2f} m/s > constraint "
                f"{max_tip_c.display_value or max_tip_c.value:.2f} m/s"
            )
        if max_pv_c is not None and pv_q is not None and pv_q.value > max_pv_c.value:
            constraint_violations.append(
                f"Criterion {row.criterion_id} yields P/V = "
                f"{pv_q.display_value or pv_q.value:.1f} W/m³ > constraint "
                f"{max_pv_c.display_value or max_pv_c.value:.1f} W/m³"
            )
        if max_vvm_c is not None and vvm_q is not None and vvm_q.value > max_vvm_c.value:
            constraint_violations.append(
                f"Criterion {row.criterion_id} yields vvm = "
                f"{vvm_q.display_value or vvm_q.value:.2f} vvm > constraint "
                f"{max_vvm_c.display_value or max_vvm_c.value:.2f} vvm"
            )
        for desc_key, ratio_val in row.descriptor_ratios.items():
            band = _lookup_band(thresh, desc_key)
            if band is not None and ratio_val is not None:
                if band.min_ratio is not None and ratio_val < band.min_ratio:
                    constraint_violations.append(
                        f"Criterion {row.criterion_id} {desc_key} target/source ratio "
                        f"({ratio_val:.2f}x) is below configured minimum "
                        f"({band.min_ratio:.2f}x)"
                    )
                if band.max_ratio is not None and ratio_val > band.max_ratio:
                    constraint_violations.append(
                        f"Criterion {row.criterion_id} {desc_key} target/source ratio "
                        f"({ratio_val:.2f}x) exceeds configured maximum "
                        f"({band.max_ratio:.2f}x)"
                    )

    if constraint_violations:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-001",
                rule_version="1.0.0",
                category="mixing",
                severity="high",
                outcome="triggered",
                title=RULE_REGISTRY["R-MIX-001"].title,
                explanation="; ".join(constraint_violations) + ".",
                input_refs=[InputRef(kind="scenario_input", key="constraints_and_criteria")],
                evidence_gap=(
                    "Bioprocess engineer review of conflicting scale-up criteria (constant P/V vs "
                    "tip speed vs aeration)."
                ),
                validation_task_codes=["VT-REVIEW-CRITERIA"],
            )
        )
    elif (
        max_tip_c is None
        and max_pv_c is None
        and max_vvm_c is None
        and not thresh.descriptor_ratio_band
    ):
        flags.append(
            RiskFlag(
                rule_id="R-MIX-001",
                rule_version="1.0.0",
                category="mixing",
                severity="low",
                outcome="not_configured",
                title=RULE_REGISTRY["R-MIX-001"].title,
                explanation=(
                    "Descriptor trade-off ratios were computed, but no process constraints (e.g., "
                    "max_tip_speed) or ratio bands are configured."
                ),
                input_refs=[InputRef(kind="scenario_input", key="constraints")],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-001",
                rule_version="1.0.0",
                category="mixing",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-MIX-001"].title,
                explanation="Computed target descriptors satisfy configured user constraints.",
                input_refs=[InputRef(kind="scenario_input", key="constraints")],
            )
        )

    # --- R-MIX-002: Mixing time evidence ---
    if not tgt.mixing_time_evidence:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-002",
                rule_version="1.0.0",
                category="mixing",
                severity="medium",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-MIX-002"].title,
                explanation=(
                    "No measured mixing-time evidence is documented for the target vessel. Larger "
                    "scale typically increases circulation and mixing times, which can cause "
                    "substrate or pH gradients during fed-batch operation."
                ),
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="mixing_time_evidence",
                    )
                ],
                evidence_gap=(
                    "Target vessel mixing time (t_95) measurement or facility characterization "
                    "report."
                ),
                validation_task_codes=["VT-MEASURE-MIXING"],
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-002",
                rule_version="1.0.0",
                category="mixing",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-MIX-002"].title,
                explanation="Target vessel includes documented mixing-time evidence.",
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="mixing_time_evidence",
                    )
                ],
            )
        )

    # --- R-MIX-003: Reynolds number turbulent check ---
    re_calcs = [
        c
        for c in calcs
        if c.formula_id == "F-RE-001" and c.status == "computed" and c.output is not None
    ]
    if not re_calcs:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-003",
                rule_version="1.0.0",
                category="mixing",
                severity="medium",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-MIX-003"].title,
                explanation=(
                    "Impeller Reynolds number could not be evaluated due to missing broth "
                    "viscosity or density."
                ),
                input_refs=[InputRef(kind="medium_property", key="viscosity")],
                evidence_gap="Broth density and dynamic viscosity at process temperature.",
                validation_task_codes=["VT-MEASURE-VISCOSITY"],
            )
        )
    elif thresh.re_turbulent_min is None:
        min_re_val = min(c.output.value for c in re_calcs if c.output is not None)
        flags.append(
            RiskFlag(
                rule_id="R-MIX-003",
                rule_version="1.0.0",
                category="mixing",
                severity="low",
                outcome="not_configured",
                title=RULE_REGISTRY["R-MIX-003"].title,
                explanation=(
                    f"Minimum computed Reynolds number is {min_re_val:,.0f}, but "
                    "'re_turbulent_min' threshold is not configured."
                ),
                input_refs=[InputRef(kind="calculation", key="F-RE-001")],
                threshold_used={"re_turbulent_min": None},
            )
        )
    else:
        low_re = [
            c
            for c in re_calcs
            if c.output is not None and c.output.value < thresh.re_turbulent_min
        ]
        if low_re:
            c0 = low_re[0]
            assert c0.output is not None
            flags.append(
                RiskFlag(
                    rule_id="R-MIX-003",
                    rule_version="1.0.0",
                    category="mixing",
                    severity="medium",
                    outcome="triggered",
                    title=RULE_REGISTRY["R-MIX-003"].title,
                    explanation=(
                        f"Computed Reynolds number ({c0.output.value:,.0f} on {c0.scale}) is below "
                        f"configured turbulent threshold ({thresh.re_turbulent_min:,.0f}); constant "
                        "turbulent power number N_p assumption may be invalid."
                    ),
                    input_refs=[InputRef(kind="calculation", key=f"F-RE-001:{c0.scale}")],
                    evidence_gap=(
                        "Verify impeller power curve in transitional flow regime and measure broth "
                        "rheology."
                    ),
                    threshold_used={"re_turbulent_min": thresh.re_turbulent_min},
                    validation_task_codes=["VT-MEASURE-VISCOSITY", "VT-REVIEW-FORMULAS"],
                )
            )
        else:
            flags.append(
                RiskFlag(
                    rule_id="R-MIX-003",
                    rule_version="1.0.0",
                    category="mixing",
                    severity="info",
                    outcome="not_triggered",
                    title=RULE_REGISTRY["R-MIX-003"].title,
                    explanation=(
                        f"All computed Reynolds numbers exceed configured turbulent threshold "
                        f"({thresh.re_turbulent_min:,.0f})."
                    ),
                    input_refs=[InputRef(kind="calculation", key="F-RE-001")],
                    threshold_used={"re_turbulent_min": thresh.re_turbulent_min},
                )
            )

    # --- R-MIX-004: Geometric similarity ---
    geo_diffs: list[str] = []
    if src.impeller_type and tgt.impeller_type and src.impeller_type != tgt.impeller_type:
        geo_diffs.append(
            f"Impeller type changes from '{src.impeller_type}' (source) to "
            f"'{tgt.impeller_type}' (target)"
        )
    if src.impeller_count and tgt.impeller_count and src.impeller_count != tgt.impeller_count:
        geo_diffs.append(
            f"Impeller count changes from {src.impeller_count} (source) to "
            f"{tgt.impeller_count} (target)"
        )

    dt_src = next(
        (
            c.output.value
            for c in calcs
            if c.formula_id == "F-GEO-001" and c.scale == "source" and c.output
        ),
        None,
    )
    dt_tgt = next(
        (
            c.output.value
            for c in calcs
            if c.formula_id == "F-GEO-001" and c.scale == "target" and c.output
        ),
        None,
    )
    hl_src = next(
        (
            c.output.value
            for c in calcs
            if c.formula_id == "F-GEO-002" and c.scale == "source" and c.output
        ),
        None,
    )
    hl_tgt = next(
        (
            c.output.value
            for c in calcs
            if c.formula_id == "F-GEO-002" and c.scale == "target" and c.output
        ),
        None,
    )

    d_tol = _d_over_t_tolerance(thresh)
    hl_tol = _hl_over_t_tolerance(thresh)
    if dt_src is not None and dt_tgt is not None and d_tol is not None:
        rel_dt = abs(dt_tgt - dt_src) / dt_src if dt_src > 0 else 0.0
        if rel_dt > d_tol:
            geo_diffs.append(
                f"D/T ratio differs by {rel_dt * 100:.1f}% ({dt_src:.2f} vs {dt_tgt:.2f})"
            )
    if hl_src is not None and hl_tgt is not None and hl_tol is not None:
        rel_hl = abs(hl_tgt - hl_src) / hl_src if hl_src > 0 else 0.0
        if rel_hl > hl_tol:
            geo_diffs.append(
                f"H_L/T ratio differs by {rel_hl * 100:.1f}% ({hl_src:.2f} vs {hl_tgt:.2f})"
            )

    if geo_diffs:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-004",
                rule_version="1.0.0",
                category="mixing",
                severity="medium",
                outcome="triggered",
                title=RULE_REGISTRY["R-MIX-004"].title,
                explanation=(
                    "; ".join(geo_diffs)
                    + ". Flow patterns and shear profiles may shift independently of bulk scale-up "
                    "criteria."
                ),
                input_refs=[
                    InputRef(kind="vessel_parameter", ref_id=src.vessel_version_id, key="geometry"),
                    InputRef(kind="vessel_parameter", ref_id=tgt.vessel_version_id, key="geometry"),
                ],
                evidence_gap=(
                    "Bioprocess engineer review of impeller and geometric differences between "
                    "source and target vessels."
                ),
                validation_task_codes=["VT-REVIEW-GEOMETRY"],
            )
        )
    elif dt_src is None or dt_tgt is None:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-004",
                rule_version="1.0.0",
                category="mixing",
                severity="low",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-MIX-004"].title,
                explanation=(
                    "Vessel inner diameter T or impeller diameter D is missing; geometric "
                    "similarity ratios cannot be fully compared."
                ),
                input_refs=[InputRef(kind="calculation", key="F-GEO-001")],
                evidence_gap="Document inner tank diameter T and impeller diameter D for both vessels.",
                validation_task_codes=["VT-DATA-VESSEL-SPEC"],
            )
        )
    elif d_tol is None and hl_tol is None:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-004",
                rule_version="1.0.0",
                category="mixing",
                severity="low",
                outcome="not_configured",
                title=RULE_REGISTRY["R-MIX-004"].title,
                explanation=(
                    "Geometric similarity ratios were computed, but no "
                    "'geometric_similarity_tolerance' is configured."
                ),
                input_refs=[InputRef(kind="calculation", key="F-GEO-001")],
                threshold_used={"geometric_similarity_tolerance": None},
            )
        )
    else:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-004",
                rule_version="1.0.0",
                category="mixing",
                severity="info",
                outcome="not_triggered",
                title=RULE_REGISTRY["R-MIX-004"].title,
                explanation=(
                    "Source and target vessels share matching impeller type and count, and "
                    "geometric ratios are within configured tolerances."
                ),
                input_refs=[InputRef(kind="calculation", key="F-GEO-001")],
            )
        )

    return flags


__all__ = ["evaluate_mix_rules"]
