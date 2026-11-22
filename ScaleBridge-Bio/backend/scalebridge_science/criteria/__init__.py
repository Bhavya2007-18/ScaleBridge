"""Scale-up criteria and descriptor trade-off computation (docs/11_SCALE_UP_CALCULATIONS.md §8)."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel

from scalebridge_science.contracts import (
    AssessmentInput,
    CalculationResult,
    KlaEvidencePoint,
    Quantity,
    TradeOffRow,
)
from scalebridge_science.formulas import (
    calc_d_over_t,
    calc_do_concentration,
    calc_hl_over_t,
    calc_otr,
    calc_otr_max,
    calc_power_per_volume,
    calc_reynolds,
    calc_superficial_gas_velocity,
    calc_tip_speed,
    calc_ungassed_power,
    calc_vvm,
)
from scalebridge_science.units import convert_value


class CriterionMetadata(BaseModel):
    criterion_id: str
    name: str
    kind: str  # "agitation" | "aeration" | "evaluation"
    equation_text: str
    description: str


CRITERIA_REGISTRY: dict[str, CriterionMetadata] = {
    "S-PV": CriterionMetadata(
        criterion_id="S-PV",
        name="Constant Power per Volume (P/V)",
        kind="agitation",
        equation_text="N_t = [ (P/V)_s · V_t / (n_imp,t · N_p,t · ρ · D_t⁵) ]^(1/3)",
        description="Solves for target agitation speed N_t that preserves source power per working volume.",
    ),
    "S-TIP": CriterionMetadata(
        criterion_id="S-TIP",
        name="Constant Impeller Tip Speed (u_tip)",
        kind="agitation",
        equation_text="N_t = N_s · (D_s / D_t)",
        description="Solves for target agitation speed N_t that preserves impeller peripheral speed.",
    ),
    "S-VVM": CriterionMetadata(
        criterion_id="S-VVM",
        name="Constant Gas Flow per Volume (vvm)",
        kind="aeration",
        equation_text="Q_g,t = vvm_s · V_t",
        description="Solves for target gas flow rate Q_g,t that preserves volumetric aeration per liquid volume.",
    ),
    "S-VS": CriterionMetadata(
        criterion_id="S-VS",
        name="Constant Superficial Gas Velocity (v_s)",
        kind="aeration",
        equation_text="Q_g,t = v_s,s · (π · T_t² / 4)",
        description="Solves for target gas flow rate Q_g,t that preserves superficial gas velocity.",
    ),
    "S-KLA": CriterionMetadata(
        criterion_id="S-KLA",
        name="kLa / Oxygen Transfer Evidence Comparison",
        kind="evaluation",
        equation_text="Compare documented target kLa & OTR against source kLa & oxygen demand",
        description="Evaluates documented kLa evidence without extrapolating unvalidated kLa correlations.",
    ),
}


def find_kla_point(
    points: list[KlaEvidencePoint], selected_id: str | None
) -> KlaEvidencePoint | None:
    if not points:
        return None
    if selected_id:
        for pt in points:
            if pt.id == selected_id:
                return pt
        return None
    return points[0]


def check_kla_mismatch_warnings(
    pt: KlaEvidencePoint,
    N_eval: Quantity | None,
    Q_g_eval: Quantity | None,
    V_w_eval: Quantity | None,
) -> list[str]:
    warnings: list[str] = []
    if pt.agitation_speed is not None and N_eval is not None and pt.agitation_speed.value > 0:
        rel = abs(N_eval.value - pt.agitation_speed.value) / pt.agitation_speed.value
        if rel > 0.05:
            warnings.append(
                f"KLA_CONDITIONS_MISMATCH: Selected kLa point '{pt.id}' was recorded at N={pt.agitation_speed.display_value or pt.agitation_speed.value:.2f} {pt.agitation_speed.display_unit or pt.agitation_speed.unit}, whereas evaluated operating point has N={N_eval.display_value or N_eval.value:.2f} {N_eval.display_unit or N_eval.unit}."
            )
    if pt.gas_flow is not None and Q_g_eval is not None and pt.gas_flow.value > 0:
        rel = abs(Q_g_eval.value - pt.gas_flow.value) / pt.gas_flow.value
        if rel > 0.05:
            warnings.append(
                f"KLA_CONDITIONS_MISMATCH: Selected kLa point '{pt.id}' was recorded at Q_g={pt.gas_flow.display_value or pt.gas_flow.value:.3f} {pt.gas_flow.display_unit or pt.gas_flow.unit}, whereas evaluated operating point has Q_g={Q_g_eval.display_value or Q_g_eval.value:.3f} {Q_g_eval.display_unit or Q_g_eval.unit}."
            )
    if pt.working_volume is not None and V_w_eval is not None and pt.working_volume.value > 0:
        rel = abs(V_w_eval.value - pt.working_volume.value) / pt.working_volume.value
        if rel > 0.05:
            warnings.append(
                f"KLA_CONDITIONS_MISMATCH: Selected kLa point '{pt.id}' was recorded at working volume {pt.working_volume.display_value or pt.working_volume.value:.2f} {pt.working_volume.display_unit or pt.working_volume.unit}."
            )
    return warnings


def evaluate_criteria_and_calculations(
    inp: AssessmentInput,
) -> tuple[list[CalculationResult], list[TradeOffRow]]:
    """Compute source baseline descriptors, target criteria operating points, and trade-offs."""
    calcs: list[CalculationResult] = []
    trade_offs: list[TradeOffRow] = []

    src_v = inp.source_vessel
    tgt_v = inp.target_vessel
    proc = inp.process
    med = inp.medium
    scen = inp.scenario

    # 1. Source operating inputs
    N_s = proc.operating.get("agitation_speed")
    Q_g_s = proc.operating.get("airflow") or proc.operating.get("gas_flow_total")
    V_s = proc.operating.get("working_volume") or src_v.parameters.get("working_volume_max")
    P_measured_s = proc.operating.get("power_draw")
    DO_req = (
        scen.constraints.get("min_do_required")
        or proc.operating.get("do_setpoint")
        or proc.extremes.get("do_min")
    )

    D_s = src_v.parameters.get("impeller_diameter")
    T_s = src_v.parameters.get("vessel_inner_diameter")
    HL_s = src_v.parameters.get("liquid_height_at_working_volume")
    Np_s = src_v.parameters.get("impeller_power_number")

    D_t = tgt_v.parameters.get("impeller_diameter")
    T_t = tgt_v.parameters.get("vessel_inner_diameter")
    HL_t = tgt_v.parameters.get("liquid_height_at_working_volume")
    Np_t = tgt_v.parameters.get("impeller_power_number")
    V_t = scen.target_working_volume

    rho = med.density
    mu = med.viscosity
    C_star = med.oxygen_saturation_concentration

    # Geometric ratios
    calcs.append(calc_d_over_t(D_s, T_s, scale="source"))
    calcs.append(calc_hl_over_t(HL_s, T_s, scale="source"))
    calcs.append(calc_d_over_t(D_t, T_t, scale="target"))
    calcs.append(calc_hl_over_t(HL_t, T_t, scale="target"))

    # Source hydrodynamic & aeration descriptors
    res_tip_s = calc_tip_speed(N_s, D_s, scale="source")
    res_re_s = calc_reynolds(rho, N_s, D_s, mu, scale="source")
    res_pwr_s = calc_ungassed_power(Np_s, rho, N_s, D_s, src_v.impeller_count, scale="source")
    P_for_pv_s = P_measured_s if P_measured_s is not None else res_pwr_s.output
    res_pv_s = calc_power_per_volume(P_for_pv_s, V_s, scale="source")
    res_vvm_s = calc_vvm(Q_g_s, V_s, scale="source")
    res_vs_s = calc_superficial_gas_velocity(Q_g_s, T_s, scale="source")
    res_doc_s = calc_do_concentration(DO_req, C_star, scale="source")

    src_kla_pt = find_kla_point(src_v.kla_evidence, scen.source_kla_point_id)
    src_kla_qty = src_kla_pt.kla if src_kla_pt else None
    src_kla_warns = check_kla_mismatch_warnings(src_kla_pt, N_s, Q_g_s, V_s) if src_kla_pt else []
    res_otr_s = calc_otr(
        src_kla_qty, C_star, res_doc_s.output, scale="source", extra_warnings=src_kla_warns
    )
    res_otr_max_s = calc_otr_max(src_kla_qty, C_star, scale="source", extra_warnings=src_kla_warns)

    calcs.extend(
        [
            res_tip_s,
            res_re_s,
            res_pwr_s,
            res_pv_s,
            res_vvm_s,
            res_vs_s,
            res_doc_s,
            res_otr_s,
            res_otr_max_s,
        ]
    )

    # Target gas flow from selected aeration basis
    Q_g_t: Quantity | None = None
    aeration_missing: list[str] = []
    if scen.aeration_basis == "S-VVM":
        if res_vvm_s.output is not None and V_t is not None:
            q_val = res_vvm_s.output.value * V_t.value
            Q_g_t = Quantity(
                value=q_val,
                unit="m**3 / second",
                original_value=convert_value(q_val, "m**3 / second", "L/min"),
                original_unit="L/min",
                display_value=convert_value(q_val, "m**3 / second", "L/min"),
                display_unit="L/min",
                provenance="calculated",
                value_nature="calculated",
                source_ref="S-VVM",
            )
        else:
            aeration_missing.extend(res_vvm_s.missing_inputs or ["vvm (source)"])
    elif scen.aeration_basis == "S-VS":
        if res_vs_s.output is not None and T_t is not None:
            area_t = math.pi * (T_t.value**2) / 4.0
            q_val = res_vs_s.output.value * area_t
            Q_g_t = Quantity(
                value=q_val,
                unit="m**3 / second",
                original_value=convert_value(q_val, "m**3 / second", "L/min"),
                original_unit="L/min",
                display_value=convert_value(q_val, "m**3 / second", "L/min"),
                display_unit="L/min",
                provenance="calculated",
                value_nature="calculated",
                source_ref="S-VS",
            )
        else:
            if res_vs_s.output is None:
                aeration_missing.extend(res_vs_s.missing_inputs or ["v_s (source)"])
            if T_t is None:
                aeration_missing.append("T_t (target vessel_inner_diameter)")

    tgt_kla_pt = find_kla_point(tgt_v.kla_evidence, scen.target_kla_point_id)
    tgt_kla_qty = tgt_kla_pt.kla if tgt_kla_pt else None

    # Helper to compute ratio safely
    def _ratio(tgt_res: CalculationResult, src_res: CalculationResult) -> float | None:
        if tgt_res.output is not None and src_res.output is not None and src_res.output.value != 0:
            return tgt_res.output.value / src_res.output.value
        return None

    # Evaluate each selected criterion
    for crit in scen.criteria:
        cid = crit.criterion_id
        cmeta = CRITERIA_REGISTRY[cid]
        N_t: Quantity | None = None
        crit_missing: list[str] = []
        crit_assumptions: list[str] = [cmeta.equation_text]
        crit_warnings: list[str] = []

        if cid == "S-TIP":
            if N_s is None:
                crit_missing.append("N_s (source agitation_speed)")
            if D_s is None:
                crit_missing.append("D_s (source impeller_diameter)")
            if D_t is None:
                crit_missing.append("D_t (target impeller_diameter)")
            if not crit_missing and N_s is not None and D_s is not None and D_t is not None:
                nt_val = N_s.value * (D_s.value / D_t.value)
                N_t = Quantity(
                    value=nt_val,
                    unit="1 / second",
                    original_value=convert_value(nt_val, "1 / second", "rpm"),
                    original_unit="rpm",
                    display_value=convert_value(nt_val, "1 / second", "rpm"),
                    display_unit="rpm",
                    provenance="calculated",
                    value_nature="calculated",
                    source_ref="S-TIP",
                )
        elif cid == "S-PV":
            if res_pv_s.output is None:
                crit_missing.extend(
                    res_pv_s.missing_inputs or ["(P/V)_s (source power per volume)"]
                )
            if V_t is None:
                crit_missing.append("V_t (target_working_volume)")
            if Np_t is None:
                crit_missing.append("N_p,t (target impeller_power_number)")
            if rho is None:
                crit_missing.append("ρ (medium.density)")
            if D_t is None:
                crit_missing.append("D_t (target impeller_diameter)")
            if (
                not crit_missing
                and res_pv_s.output is not None
                and V_t is not None
                and Np_t is not None
                and rho is not None
                and D_t is not None
            ):
                n_imp_t = max(1, tgt_v.impeller_count or 1)
                denom = float(n_imp_t) * Np_t.value * rho.value * (D_t.value**5)
                if denom <= 0:
                    crit_missing.append("Positive N_p,t · ρ · D_t⁵")
                else:
                    nt_val = ((res_pv_s.output.value * V_t.value) / denom) ** (1.0 / 3.0)
                    N_t = Quantity(
                        value=nt_val,
                        unit="1 / second",
                        original_value=convert_value(nt_val, "1 / second", "rpm"),
                        original_unit="rpm",
                        display_value=convert_value(nt_val, "1 / second", "rpm"),
                        display_unit="rpm",
                        provenance="calculated",
                        value_nature="calculated",
                        source_ref="S-PV",
                    )
                    crit_assumptions.append(
                        "Target N_t derived from ungassed turbulent power equation P₀ = n_imp·N_p·ρ·N³·D⁵."
                    )
        elif cid == "S-KLA":
            if tgt_kla_pt is None:
                crit_missing.append("kLa (target vessel kLa evidence point)")
            else:
                N_t = tgt_kla_pt.agitation_speed
                if N_t is None:
                    crit_warnings.append(
                        "Target kLa evidence point does not specify the agitation speed N at which kLa was measured."
                    )

        # Evaluate target descriptors under (N_t, Q_g_t, V_t)
        res_tip_t = calc_tip_speed(N_t, D_t, scale="target", criterion_id=cid)
        res_re_t = calc_reynolds(rho, N_t, D_t, mu, scale="target", criterion_id=cid)
        res_pwr_t = calc_ungassed_power(
            Np_t, rho, N_t, D_t, tgt_v.impeller_count, scale="target", criterion_id=cid
        )
        res_pv_t = calc_power_per_volume(res_pwr_t.output, V_t, scale="target", criterion_id=cid)
        res_vvm_t = calc_vvm(Q_g_t, V_t, scale="target", criterion_id=cid)
        res_vs_t = calc_superficial_gas_velocity(Q_g_t, T_t, scale="target", criterion_id=cid)

        tgt_kla_warns = (
            check_kla_mismatch_warnings(tgt_kla_pt, N_t, Q_g_t, V_t) if tgt_kla_pt else []
        )
        res_otr_t = calc_otr(
            tgt_kla_qty,
            C_star,
            res_doc_s.output,
            scale="target",
            criterion_id=cid,
            extra_warnings=tgt_kla_warns,
        )
        res_otr_max_t = calc_otr_max(
            tgt_kla_qty,
            C_star,
            scale="target",
            criterion_id=cid,
            extra_warnings=tgt_kla_warns,
        )

        calcs.extend(
            [
                res_tip_t,
                res_re_t,
                res_pwr_t,
                res_pv_t,
                res_vvm_t,
                res_vs_t,
                res_otr_t,
                res_otr_max_t,
            ]
        )

        op_point: dict[str, Quantity] = {"V_w": V_t}
        if N_t is not None:
            op_point["N"] = N_t
        if Q_g_t is not None:
            op_point["Q_g"] = Q_g_t

        descriptors_target = {
            "P_per_V": res_pv_t.output,
            "P_0": res_pwr_t.output,
            "u_tip": res_tip_t.output,
            "Re": res_re_t.output,
            "vvm": res_vvm_t.output,
            "v_s": res_vs_t.output,
            "OTR": res_otr_t.output,
            "OTR_max": res_otr_max_t.output,
        }
        descriptor_ratios = {
            "P_per_V": _ratio(res_pv_t, res_pv_s),
            "u_tip": _ratio(res_tip_t, res_tip_s),
            "Re": _ratio(res_re_t, res_re_s),
            "vvm": _ratio(res_vvm_t, res_vvm_s),
            "v_s": _ratio(res_vs_t, res_vs_s),
            "OTR": _ratio(res_otr_t, res_otr_s),
        }

        row_status: Literal["computed", "insufficient_evidence", "not_applicable", "error"] = (
            "insufficient_evidence" if crit_missing else "computed"
        )
        trade_offs.append(
            TradeOffRow(
                criterion_id=cid,
                criterion_name=cmeta.name,
                is_primary=crit.is_primary,
                status=row_status,
                missing_inputs=crit_missing + aeration_missing,
                target_operating_point=op_point,
                descriptors_target=descriptors_target,
                descriptor_ratios=descriptor_ratios,
                assumptions=crit_assumptions,
                warnings=crit_warnings + tgt_kla_warns,
            )
        )

    return calcs, trade_offs
