"""Equipment compatibility checks (C-*) (docs/13 §4)."""

from __future__ import annotations

from scalebridge_science.contracts import (
    AssessmentInput,
    CompatibilityCheck,
    InputRef,
    Quantity,
    TradeOffRow,
    VesselSpec,
)
from scalebridge_science.units import convert_value

REQUIRED_VESSEL_SPEC_KEYS: list[tuple[str, list[str], list[str]]] = [
    ("working_volume_min", [], ["C-VOLUME-RANGE"]),
    ("working_volume_max", ["F-PV-001", "F-VVM-001"], ["C-VOLUME-RANGE"]),
    ("vessel_inner_diameter", ["F-VS-001", "F-GEO-001", "F-GEO-002"], []),
    ("liquid_height_at_working_volume", ["F-GEO-002"], []),
    ("impeller_diameter", ["F-TIP-001", "F-RE-001", "F-PWR-001", "F-GEO-001"], []),
    ("impeller_power_number", ["F-PWR-001"], ["C-MOTOR-POWER"]),
    ("agitation_speed_min", [], ["C-AGIT-RANGE"]),
    ("agitation_speed_max", [], ["C-AGIT-RANGE"]),
    ("motor_power_limit", [], ["C-MOTOR-POWER"]),
    ("gas_flow_min", [], ["C-GAS-RANGE"]),
    ("gas_flow_max", [], ["C-GAS-RANGE"]),
    ("cooling_capacity", [], ["C-COOLING"]),
]


def inspect_missing_vessel_specs(vessel: VesselSpec) -> list[dict[str, object]]:
    missing: list[dict[str, object]] = []
    for key, req_formulas, req_checks in REQUIRED_VESSEL_SPEC_KEYS:
        if key not in vessel.parameters:
            missing.append(
                {
                    "key": key,
                    "required_by_formulas": req_formulas,
                    "required_by_checks": req_checks,
                }
            )
    if not vessel.kla_evidence:
        missing.append(
            {
                "key": "kla_evidence",
                "required_by_formulas": ["F-OTR-001", "F-OTR-MAX"],
                "required_by_checks": [],
            }
        )
    return missing


def _range_check(
    check_id: str,
    criterion_id: str | None,
    parameter_key: str,
    title: str,
    req_qty: Quantity | None,
    min_qty: Quantity | None,
    max_qty: Quantity | None,
    unit_si: str,
    display_unit: str,
    refs: list[InputRef],
) -> CompatibilityCheck:
    req_si = req_qty.value if req_qty is not None else None
    min_si = min_qty.value if min_qty is not None else None
    max_si = max_qty.value if max_qty is not None else None

    req_disp = (
        convert_value(req_si, unit_si, display_unit)
        if req_si is not None and unit_si != display_unit
        else req_si
    )
    min_disp = (
        convert_value(min_si, unit_si, display_unit)
        if min_si is not None and unit_si != display_unit
        else min_si
    )
    max_disp = (
        convert_value(max_si, unit_si, display_unit)
        if max_si is not None and unit_si != display_unit
        else max_si
    )

    if req_si is None or (min_si is None and max_si is None):
        missing_parts: list[str] = []
        if req_si is None:
            missing_parts.append("required operating value")
        if min_si is None and max_si is None:
            missing_parts.append(f"target vessel '{parameter_key}' capability limits")
        return CompatibilityCheck(
            check_id=check_id,
            criterion_id=criterion_id,
            parameter_key=parameter_key,
            title=title,
            required_value_si=req_si,
            capability_min_si=min_si,
            capability_max_si=max_si,
            unit_si=unit_si,
            display_unit=display_unit,
            required_display=req_disp,
            capability_min_display=min_disp,
            capability_max_display=max_disp,
            outcome="cannot_evaluate",
            explanation=f"Cannot evaluate {title}: missing {', '.join(missing_parts)}.",
            input_refs=refs,
        )

    below_min = min_si is not None and req_si < min_si
    above_max = max_si is not None and req_si > max_si

    if below_min or above_max:
        bounds_str = (
            f"[{min_disp:.2f}, {max_disp:.2f}] {display_unit}"
            if min_disp is not None and max_disp is not None
            else (
                f"≤ {max_disp:.2f} {display_unit}"
                if max_disp is not None
                else f"≥ {min_disp:.2f} {display_unit}"
            )
        )
        return CompatibilityCheck(
            check_id=check_id,
            criterion_id=criterion_id,
            parameter_key=parameter_key,
            title=title,
            required_value_si=req_si,
            capability_min_si=min_si,
            capability_max_si=max_si,
            unit_si=unit_si,
            display_unit=display_unit,
            required_display=req_disp,
            capability_min_display=min_disp,
            capability_max_display=max_disp,
            outcome="incompatible",
            explanation=(
                f"Required {title} ({req_disp:.2f} {display_unit}) is outside target vessel "
                f"capability ({bounds_str})."
            ),
            input_refs=refs,
        )

    bounds_str = (
        f"[{min_disp:.2f}, {max_disp:.2f}] {display_unit}"
        if min_disp is not None and max_disp is not None
        else (
            f"≤ {max_disp:.2f} {display_unit}"
            if max_disp is not None
            else f"≥ {min_disp:.2f} {display_unit}"
        )
    )
    return CompatibilityCheck(
        check_id=check_id,
        criterion_id=criterion_id,
        parameter_key=parameter_key,
        title=title,
        required_value_si=req_si,
        capability_min_si=min_si,
        capability_max_si=max_si,
        unit_si=unit_si,
        display_unit=display_unit,
        required_display=req_disp,
        capability_min_display=min_disp,
        capability_max_display=max_disp,
        outcome="compatible",
        explanation=(
            f"Required {title} ({req_disp:.2f} {display_unit}) is within target vessel "
            f"capability ({bounds_str})."
        ),
        input_refs=refs,
    )


def evaluate_compatibility_checks(
    inp: AssessmentInput,
    trade_offs: list[TradeOffRow],
) -> list[CompatibilityCheck]:
    checks: list[CompatibilityCheck] = []
    tgt = inp.target_vessel
    scen = inp.scenario
    proc = inp.process

    # 1. Working volume range (C-VOLUME-RANGE)
    v_min = tgt.parameters.get("working_volume_min")
    v_max = tgt.parameters.get("working_volume_max")
    checks.append(
        _range_check(
            check_id="C-VOLUME-RANGE",
            criterion_id=None,
            parameter_key="working_volume",
            title="Target working volume",
            req_qty=scen.target_working_volume,
            min_qty=v_min,
            max_qty=v_max,
            unit_si="m**3",
            display_unit="L",
            refs=[
                InputRef(kind="scenario_input", key="target_working_volume"),
                InputRef(
                    kind="vessel_parameter",
                    ref_id=tgt.vessel_version_id,
                    key="working_volume_min/max",
                ),
            ],
        )
    )

    # 2. Per-criterion agitation & motor power checks
    n_min = tgt.parameters.get("agitation_speed_min")
    n_max = tgt.parameters.get("agitation_speed_max")
    p_lim = tgt.parameters.get("motor_power_limit")

    for row in trade_offs:
        cid = row.criterion_id
        N_req = row.target_operating_point.get("N")
        P0_req = row.descriptors_target.get("P_0")

        checks.append(
            _range_check(
                check_id="C-AGIT-RANGE",
                criterion_id=cid,
                parameter_key="agitation_speed",
                title=f"Target agitation speed ({cid})",
                req_qty=N_req,
                min_qty=n_min,
                max_qty=n_max,
                unit_si="1 / second",
                display_unit="rpm",
                refs=[
                    InputRef(kind="calculation", key=f"N_t:{cid}"),
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="agitation_speed_min/max",
                    ),
                ],
            )
        )

        checks.append(
            _range_check(
                check_id="C-MOTOR-POWER",
                criterion_id=cid,
                parameter_key="motor_power_limit",
                title=f"Target ungassed power draw vs motor limit ({cid})",
                req_qty=P0_req,
                min_qty=None,
                max_qty=p_lim,
                unit_si="watt",
                display_unit="W",
                refs=[
                    InputRef(kind="calculation", key=f"F-PWR-001:target:{cid}"),
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="motor_power_limit",
                    ),
                ],
            )
        )

    # 3. Gas flow range (C-GAS-RANGE)
    q_min = tgt.parameters.get("gas_flow_min")
    q_max = tgt.parameters.get("gas_flow_max")
    Q_req = trade_offs[0].target_operating_point.get("Q_g") if trade_offs else None
    checks.append(
        _range_check(
            check_id="C-GAS-RANGE",
            criterion_id=scen.aeration_basis,
            parameter_key="gas_flow",
            title=f"Target sparger gas flow ({scen.aeration_basis})",
            req_qty=Q_req,
            min_qty=q_min,
            max_qty=q_max,
            unit_si="m**3 / second",
            display_unit="L/min",
            refs=[
                InputRef(kind="calculation", key=f"Q_g,t:{scen.aeration_basis}"),
                InputRef(
                    kind="vessel_parameter",
                    ref_id=tgt.vessel_version_id,
                    key="gas_flow_min/max",
                ),
            ],
        )
    )

    # 4. Cooling capacity (C-COOLING)
    q_cool = tgt.parameters.get("cooling_capacity")
    q_heat = scen.constraints.get("estimated_heat_load")
    checks.append(
        _range_check(
            check_id="C-COOLING",
            criterion_id=None,
            parameter_key="cooling_capacity",
            title="Target heat removal vs cooling capacity",
            req_qty=q_heat,
            min_qty=None,
            max_qty=q_cool,
            unit_si="watt",
            display_unit="W",
            refs=[
                InputRef(kind="scenario_input", key="estimated_heat_load"),
                InputRef(
                    kind="vessel_parameter",
                    ref_id=tgt.vessel_version_id,
                    key="cooling_capacity",
                ),
            ],
        )
    )

    # 5. Temperature range (C-TEMP-RANGE)
    t_min = tgt.parameters.get("temperature_min")
    t_max = tgt.parameters.get("temperature_max")
    t_req = proc.operating.get("temperature") or proc.operating.get("temperature_setpoint")
    checks.append(
        _range_check(
            check_id="C-TEMP-RANGE",
            criterion_id=None,
            parameter_key="temperature",
            title="Process temperature vs target vessel range",
            req_qty=t_req,
            min_qty=t_min,
            max_qty=t_max,
            unit_si="kelvin",
            display_unit="degC",
            refs=[
                InputRef(kind="measurement_summary", key="temperature"),
                InputRef(
                    kind="vessel_parameter",
                    ref_id=tgt.vessel_version_id,
                    key="temperature_min/max",
                ),
            ],
        )
    )

    # 6. Instrumentation & controls (C-INSTRUMENT)
    req_inst = set(proc.required_instruments)
    req_ctrl = set(proc.required_controls)
    if not req_inst and not req_ctrl:
        # Infer baseline probes from operating variables present
        if "ph" in proc.operating:
            req_inst.add("ph_probe")
        if "dissolved_oxygen" in proc.operating or "min_do_required" in scen.constraints:
            req_inst.add("do_probe")
        if "temperature" in proc.operating:
            req_inst.add("temperature_probe")

    missing_inst = sorted(req_inst - set(tgt.instrumentation))
    missing_ctrl = sorted(req_ctrl - set(tgt.controls))
    if not tgt.instrumentation and not tgt.controls:
        checks.append(
            CompatibilityCheck(
                check_id="C-INSTRUMENT",
                criterion_id=None,
                parameter_key="instrumentation_controls",
                title="Target instrumentation and control capabilities",
                unit_si="dimensionless",
                display_unit="dimensionless",
                outcome="cannot_evaluate",
                explanation="Target vessel instrumentation and control list is empty / undocumented.",
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="instrumentation",
                    )
                ],
            )
        )
    elif missing_inst or missing_ctrl:
        missing_all = missing_inst + missing_ctrl
        checks.append(
            CompatibilityCheck(
                check_id="C-INSTRUMENT",
                criterion_id=None,
                parameter_key="instrumentation_controls",
                title="Target instrumentation and control capabilities",
                unit_si="dimensionless",
                display_unit="dimensionless",
                outcome="incompatible",
                explanation=(
                    "Target vessel does not document required instrumentation/controls: "
                    f"{', '.join(missing_all)}."
                ),
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="instrumentation",
                    )
                ],
            )
        )
    else:
        checks.append(
            CompatibilityCheck(
                check_id="C-INSTRUMENT",
                criterion_id=None,
                parameter_key="instrumentation_controls",
                title="Target instrumentation and control capabilities",
                unit_si="dimensionless",
                display_unit="dimensionless",
                outcome="compatible",
                explanation=(
                    "Target vessel documents all required sensors/controls "
                    f"({', '.join(sorted(req_inst | req_ctrl)) or 'basic probes'})."
                ),
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="instrumentation",
                    )
                ],
            )
        )

    return checks


__all__ = [
    "REQUIRED_VESSEL_SPEC_KEYS",
    "evaluate_compatibility_checks",
    "inspect_missing_vessel_specs",
]
