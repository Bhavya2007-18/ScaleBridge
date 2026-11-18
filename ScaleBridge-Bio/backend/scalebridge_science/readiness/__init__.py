"""Equipment compatibility checks (C-*), Risk Engine rules (R-*), and Validation Planner (VT-*)."""

from __future__ import annotations

from pydantic import BaseModel

from scalebridge_science.contracts import (
    AssessmentInput,
    CalculationResult,
    CompatibilityCheck,
    InputRef,
    Quantity,
    RiskFlag,
    Severity,
    TradeOffRow,
    ValidationTaskSpec,
    VesselSpec,
)
from scalebridge_science.criteria import check_kla_mismatch_warnings, find_kla_point
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
            explanation=f"Required {title} ({req_disp:.2f} {display_unit}) is outside target vessel capability ({bounds_str}).",
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
        explanation=f"Required {title} ({req_disp:.2f} {display_unit}) is within target vessel capability ({bounds_str}).",
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
                explanation=f"Target vessel does not document required instrumentation/controls: {', '.join(missing_all)}.",
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
                explanation=f"Target vessel documents all required sensors/controls ({', '.join(sorted(req_inst | req_ctrl)) or 'basic probes'}).",
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


class RuleMetadata(BaseModel):
    rule_id: str
    version: str
    category: str
    default_severity: Severity
    title: str
    description: str


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


def evaluate_risk_rules(
    inp: AssessmentInput,
    calcs: list[CalculationResult],
    trade_offs: list[TradeOffRow],
    checks: list[CompatibilityCheck],
) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    src = inp.source_vessel
    tgt = inp.target_vessel
    proc = inp.process
    scen = inp.scenario
    thresh = scen.thresholds

    primary_cids = {c.criterion_id for c in scen.criteria if c.is_primary}

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
                explanation=f"{len(missing_calcs)} calculation(s) ({', '.join(formula_ids)}) could not be evaluated due to missing inputs: {', '.join(all_missing)}.",
                input_refs=[
                    InputRef(kind="calculation", key=f"{c.formula_id}:{c.scale}:{c.criterion_id or 'baseline'}")
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
    assumed_calcs = [c for c in calcs if c.status == "computed" and c.evidence_level == "assumed"]
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
                explanation=f"Calculations ({', '.join(fids)}) rely on one or more user-assumed physical properties rather than direct measurements.",
                input_refs=[
                    InputRef(kind="calculation", key=f"{c.formula_id}:{c.scale}")
                    for c in assumed_calcs[:6]
                ],
                evidence_gap="Replace user-assumed medium/process properties (e.g. density, viscosity, C*) with laboratory measurements.",
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
                explanation=f"Source batch data-quality checks flagged high/critical issues on: {', '.join(proc.high_severity_dq_variables)}.",
                input_refs=[
                    InputRef(kind="measurement_summary", key=v)
                    for v in proc.high_severity_dq_variables
                ],
                evidence_gap="Inspect source batch timestamp gaps, out-of-range spikes, or invalid sensor points before relying on summary statistics.",
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
                explanation=f"Calibration status is '{', '.join(f'{k}:{proc.calibration_status[k]}' for k in uncal)}'.",
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
                explanation="This assessment uses data marked as synthetic/demonstration. Outputs illustrate workflow mechanics and must not be used for physical pilot execution.",
                input_refs=[InputRef(kind="scenario_input", key="is_synthetic")],
                evidence_gap="Import a verified laboratory fermentation dataset from the actual organism and bench bioreactor.",
                validation_task_codes=["VT-DATA-REAL"],
            )
        )

    # --- R-DAT-006: Pending review formulas ---
    pending_fids = sorted({c.formula_id for c in calcs if c.review_status == "pending_review" and c.status == "computed"})
    if pending_fids:
        flags.append(
            RiskFlag(
                rule_id="R-DAT-006",
                rule_version="1.0.0",
                category="data",
                severity="info",
                outcome="triggered",
                title=RULE_REGISTRY["R-DAT-006"].title,
                explanation=f"Computed results include formula(s) with status 'pending_review': {', '.join(pending_fids)}.",
                input_refs=[InputRef(kind="calculation", key=fid) for fid in pending_fids],
                evidence_gap="Complete independent bioprocess advisor review of proposed engineering correlations.",
                validation_task_codes=["VT-REVIEW-FORMULAS"],
            )
        )

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
                evidence_gap="Provide dissolved oxygen time-series data from laboratory fermentation runs.",
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
                explanation=f"Minimum observed source DO was {do_min.value:.1f} % air sat, but neither scenario constraint 'min_do_required' nor threshold 'do_critical_percent' is configured.",
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
                explanation=f"Source batch minimum DO reached {do_min.value:.1f} % air sat, falling below required minimum DO ({do_thresh_val:.1f} % air sat). The lab process may already experience oxygen limitation.",
                input_refs=[
                    InputRef(kind="measurement_summary", key="do_min"),
                    InputRef(kind="scenario_input", key="min_do_required"),
                ],
                evidence_gap="Investigate whether transient DO dips at bench scale impacted yield and confirm critical DO threshold.",
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
                explanation=f"Source batch minimum DO ({do_min.value:.1f} % air sat) remained at or above required threshold ({do_thresh_val:.1f} % air sat).",
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
                explanation="Target vessel profile has no documented kLa evidence point. Target oxygen transfer rate (OTR) cannot be evaluated.",
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="kla_evidence",
                    )
                ],
                evidence_gap="Measured kLa in target vessel across planned agitation and aeration operating envelope.",
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
                explanation=f"Target vessel kLa evidence point '{tgt_kla.id}' ({tgt_kla.kla.display_value or tgt_kla.kla.value:.1f} {tgt_kla.kla.display_unit or tgt_kla.kla.unit}) is available.",
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
                evidence_gap="Characterize baseline kLa in the source laboratory vessel at reference operating conditions.",
                validation_task_codes=["VT-KLA-SOURCE"],
            )
        )

    # --- R-OXY-003: Target OTR vs Peak OUR ---
    our_max = proc.extremes.get("our_max")
    otr_targets = [
        c
        for c in calcs
        if c.formula_id == "F-OTR-001" and c.scale == "target" and c.status == "computed" and c.output is not None
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
                explanation=f"Cannot compare target oxygen transfer capacity against process oxygen demand: missing {', '.join(missing_oxy)}.",
                input_refs=[
                    InputRef(kind="measurement_summary", key="our_max"),
                    InputRef(kind="calculation", key="F-OTR-001:target"),
                ],
                evidence_gap=f"Quantify {', '.join(missing_oxy)} to verify oxygen transfer adequacy before pilot scale-up.",
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
        failing = [c for c in otr_targets if c.output is not None and c.output.value < required_otr_si]
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
                    explanation=f"Target OTR at required DO ({otr_disp:.2f} mmol/(L·h)) is below required oxygen demand ({req_disp:.2f} mmol/(L·h), based on peak OUR {our_disp:.2f} mmol/(L·h) and margin {margin*100:.0f}%).",
                    input_refs=[
                        InputRef(kind="calculation", key=f"F-OTR-001:target:{c0.criterion_id}"),
                        InputRef(kind="measurement_summary", key="our_max"),
                    ],
                    evidence_gap="Verify target kLa at higher agitation/aeration or evaluate oxygen enrichment / headpressure strategy with a bioprocess engineer.",
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
                    explanation=f"Evaluated target OTR ({otr_disp:.2f} mmol/(L·h)) meets or exceeds peak oxygen demand ({req_disp:.2f} mmol/(L·h)).",
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
                f"Target kLa provenance is '{tgt_kla.kla.provenance}' rather than a physical measurement in the target vessel."
            )
        if tgt_kla.medium_description and "water" in tgt_kla.medium_description.lower():
            mismatch_reasons.append(
                f"Target kLa was characterized in '{tgt_kla.medium_description}', which may differ from coalescing/non-coalescing fermentation broth."
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
                    evidence_gap="Validate kLa in the target vessel at the planned (N, Q_g, V_w) operating point and account for medium effects.",
                    validation_task_codes=["VT-KLA-TARGET", "VT-REVIEW-OXY"],
                )
            )

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
                f"Criterion {row.criterion_id} yields u_tip = {u_tip_q.display_value or u_tip_q.value:.2f} m/s > constraint {max_tip_c.display_value or max_tip_c.value:.2f} m/s"
            )
        if max_pv_c is not None and pv_q is not None and pv_q.value > max_pv_c.value:
            constraint_violations.append(
                f"Criterion {row.criterion_id} yields P/V = {pv_q.display_value or pv_q.value:.1f} W/m³ > constraint {max_pv_c.display_value or max_pv_c.value:.1f} W/m³"
            )
        if max_vvm_c is not None and vvm_q is not None and vvm_q.value > max_vvm_c.value:
            constraint_violations.append(
                f"Criterion {row.criterion_id} yields vvm = {vvm_q.display_value or vvm_q.value:.2f} vvm > constraint {max_vvm_c.display_value or max_vvm_c.value:.2f} vvm"
            )
        for desc_key, ratio_val in row.descriptor_ratios.items():
            band = thresh.descriptor_ratio_band.get(desc_key)
            if band and ratio_val is not None:
                if band.min_ratio is not None and ratio_val < band.min_ratio:
                    constraint_violations.append(
                        f"Criterion {row.criterion_id} {desc_key} target/source ratio ({ratio_val:.2f}x) is below configured minimum ({band.min_ratio:.2f}x)"
                    )
                if band.max_ratio is not None and ratio_val > band.max_ratio:
                    constraint_violations.append(
                        f"Criterion {row.criterion_id} {desc_key} target/source ratio ({ratio_val:.2f}x) exceeds configured maximum ({band.max_ratio:.2f}x)"
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
                evidence_gap="Bioprocess engineer review of conflicting scale-up criteria (constant P/V vs tip speed vs aeration).",
                validation_task_codes=["VT-REVIEW-CRITERIA"],
            )
        )
    elif max_tip_c is None and max_pv_c is None and max_vvm_c is None and not thresh.descriptor_ratio_band:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-001",
                rule_version="1.0.0",
                category="mixing",
                severity="low",
                outcome="not_configured",
                title=RULE_REGISTRY["R-MIX-001"].title,
                explanation="Descriptor trade-off ratios were computed, but no process constraints (e.g., max_tip_speed) or ratio bands are configured.",
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
                explanation="No measured mixing-time evidence is documented for the target vessel. Larger scale typically increases circulation and mixing times, which can cause substrate or pH gradients during fed-batch operation.",
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="mixing_time_evidence",
                    )
                ],
                evidence_gap="Target vessel mixing time (t_95) measurement or facility characterization report.",
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
    re_calcs = [c for c in calcs if c.formula_id == "F-RE-001" and c.status == "computed" and c.output is not None]
    if not re_calcs:
        flags.append(
            RiskFlag(
                rule_id="R-MIX-003",
                rule_version="1.0.0",
                category="mixing",
                severity="medium",
                outcome="insufficient_evidence",
                title=RULE_REGISTRY["R-MIX-003"].title,
                explanation="Impeller Reynolds number could not be evaluated due to missing broth viscosity or density.",
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
                explanation=f"Minimum computed Reynolds number is {min_re_val:,.0f}, but 're_turbulent_min' threshold is not configured.",
                input_refs=[InputRef(kind="calculation", key="F-RE-001")],
                threshold_used={"re_turbulent_min": None},
            )
        )
    else:
        low_re = [c for c in re_calcs if c.output is not None and c.output.value < thresh.re_turbulent_min]
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
                    explanation=f"Computed Reynolds number ({c0.output.value:,.0f} on {c0.scale}) is below configured turbulent threshold ({thresh.re_turbulent_min:,.0f}); constant turbulent power number N_p assumption may be invalid.",
                    input_refs=[InputRef(kind="calculation", key=f"F-RE-001:{c0.scale}")],
                    evidence_gap="Verify impeller power curve in transitional flow regime and measure broth rheology.",
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
                    explanation=f"All computed Reynolds numbers exceed configured turbulent threshold ({thresh.re_turbulent_min:,.0f}).",
                    input_refs=[InputRef(kind="calculation", key="F-RE-001")],
                    threshold_used={"re_turbulent_min": thresh.re_turbulent_min},
                )
            )

    # --- R-MIX-004: Geometric similarity ---
    geo_diffs: list[str] = []
    if src.impeller_type and tgt.impeller_type and src.impeller_type != tgt.impeller_type:
        geo_diffs.append(
            f"Impeller type changes from '{src.impeller_type}' (source) to '{tgt.impeller_type}' (target)"
        )
    if src.impeller_count and tgt.impeller_count and src.impeller_count != tgt.impeller_count:
        geo_diffs.append(
            f"Impeller count changes from {src.impeller_count} (source) to {tgt.impeller_count} (target)"
        )

    dt_src = next((c.output.value for c in calcs if c.formula_id == "F-GEO-001" and c.scale == "source" and c.output), None)
    dt_tgt = next((c.output.value for c in calcs if c.formula_id == "F-GEO-001" and c.scale == "target" and c.output), None)
    if dt_src is not None and dt_tgt is not None and thresh.d_over_t_rel_tol is not None:
        rel_dt = abs(dt_tgt - dt_src) / dt_src if dt_src > 0 else 0.0
        if rel_dt > thresh.d_over_t_rel_tol:
            geo_diffs.append(
                f"D/T ratio differs by {rel_dt*100:.1f}% ({dt_src:.2f} vs {dt_tgt:.2f})"
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
                explanation="; ".join(geo_diffs) + ". Flow patterns and shear profiles may shift independently of bulk scale-up criteria.",
                input_refs=[
                    InputRef(kind="vessel_parameter", ref_id=src.vessel_version_id, key="geometry"),
                    InputRef(kind="vessel_parameter", ref_id=tgt.vessel_version_id, key="geometry"),
                ],
                evidence_gap="Bioprocess engineer review of impeller and geometric differences between source and target vessels.",
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
                explanation="Vessel inner diameter T or impeller diameter D is missing; geometric similarity ratios cannot be fully compared.",
                input_refs=[InputRef(kind="calculation", key="F-GEO-001")],
                evidence_gap="Document inner tank diameter T and impeller diameter D for both vessels.",
                validation_task_codes=["VT-DATA-VESSEL-SPEC"],
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
                explanation="Source and target vessels share matching impeller type and count.",
                input_refs=[InputRef(kind="calculation", key="F-GEO-001")],
            )
        )

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
                explanation="Target vessel cooling capacity is not documented. Heat removal often becomes limiting at larger scale due to lower surface-area-to-volume ratio.",
                input_refs=[
                    InputRef(
                        kind="vessel_parameter",
                        ref_id=tgt.vessel_version_id,
                        key="cooling_capacity",
                    )
                ],
                evidence_gap="Obtain target jacket/coil cooling capacity (in W or kW at process temperature) from facility or vendor.",
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
                explanation=f"Target vessel cooling capacity is documented ({q_cool.display_value or q_cool.value:.1f} {q_cool.display_unit or q_cool.unit}).",
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
                    explanation=f"Estimated heat load with margin ({req_cool:.0f} W) exceeds target cooling capacity ({q_cool.value:.0f} W).",
                    input_refs=[
                        InputRef(kind="scenario_input", key="estimated_heat_load"),
                        InputRef(
                            kind="vessel_parameter",
                            ref_id=tgt.vessel_version_id,
                            key="cooling_capacity",
                        ),
                    ],
                    evidence_gap="Perform detailed metabolic + agitation heat balance and review cooling utility supply temperature.",
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
                    explanation=f"Target cooling capacity ({q_cool.value:.0f} W) exceeds estimated heat load ({req_cool:.0f} W).",
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
                explanation="Cannot evaluate thermal balance because estimated heat load or target cooling capacity is not provided.",
                input_refs=[InputRef(kind="scenario_input", key="estimated_heat_load")],
                evidence_gap="Provide estimated peak metabolic + mechanical heat load and target cooling capacity.",
                validation_task_codes=["VT-REVIEW-THERMAL", "VT-DATA-COOLING"],
            )
        )

    # --- R-EQP-001..006 from compatibility checks ---
    check_to_rule = {
        "C-AGIT-RANGE": ("R-EQP-001", ["VT-REVIEW-EQUIPMENT"]),
        "C-MOTOR-POWER": ("R-EQP-002", ["VT-REVIEW-EQUIPMENT", "VT-MEASURE-POWER"]),
        "C-GAS-RANGE": ("R-EQP-003", ["VT-REVIEW-EQUIPMENT"]),
        "C-VOLUME-RANGE": ("R-EQP-004", ["VT-REVIEW-EQUIPMENT"]),
        "C-INSTRUMENT": ("R-EQP-005", ["VT-REVIEW-EQUIPMENT"]),
    }
    for chk in checks:
        mapping = check_to_rule.get(chk.check_id)
        if not mapping:
            continue
        rid, tcodes = mapping
        rmeta = RULE_REGISTRY[rid]
        if chk.outcome == "incompatible":
            is_prim = chk.criterion_id is None or chk.criterion_id in primary_cids
            sev: Severity = "critical" if is_prim and rmeta.default_severity == "critical" else "high"
            flags.append(
                RiskFlag(
                    rule_id=rid,
                    rule_version=rmeta.version,
                    category="equipment",
                    severity=sev,
                    outcome="triggered",
                    title=f"{rmeta.title}" + (f" ({chk.criterion_id})" if chk.criterion_id else ""),
                    explanation=chk.explanation,
                    input_refs=chk.input_refs,
                    evidence_gap="Adjust target operating point/volume, select an alternative criterion, or verify if target vessel hardware can be reconfigured.",
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
                explanation=f"Equipment compatibility check(s) ({c_names}) could not be evaluated due to missing vessel capability limits or missing operating point inputs.",
                input_refs=[
                    InputRef(kind="compatibility_check", key=c.check_id)
                    for c in cannot_eval_checks
                ],
                evidence_gap="Complete target vessel capability envelope (min/max agitation, motor power, gas flow, cooling, instrumentation).",
                validation_task_codes=["VT-DATA-VESSEL-SPEC"],
            )
        )

    return flags


VALIDATION_TASK_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "VT-KLA-TARGET": (
        "measurement",
        "P1",
        "Measure or obtain verified kLa in target vessel across planned (N, Q_g) range",
        "Conduct dynamic gassing-out or sulfite kLa characterization in the target vessel (or obtain verified facility test data) covering the target agitation and aeration operating point.",
    ),
    "VT-KLA-SOURCE": (
        "measurement",
        "P2",
        "Measure kLa in source laboratory vessel at reference operating point",
        "Determine baseline kLa in the laboratory vessel at the process agitation and airflow setpoints to anchor oxygen transfer comparisons.",
    ),
    "VT-MEASURE-OUR": (
        "measurement",
        "P1",
        "Quantify peak oxygen uptake rate (OUR) in laboratory process",
        "Measure peak OUR via exhaust gas O₂/CO₂ analysis or dynamic DO depletion during peak metabolic phase.",
    ),
    "VT-EXP-DO-PROFILE": (
        "experiment",
        "P2",
        "Verify DO sensitivity and minimum acceptable DO in bench-scale run",
        "Review bench-scale DO profiles and determine critical DO threshold below which specific productivity or viability degrades.",
    ),
    "VT-REVIEW-OXY": (
        "expert_review",
        "P1",
        "Bioprocess engineer review of oxygen transfer balance and gas supply strategy",
        "Review OTR = kLa(C* - C_L) driving force, headpressure effects, and O₂ enrichment options with a senior bioprocess engineer.",
    ),
    "VT-REVIEW-CRITERIA": (
        "expert_review",
        "P1",
        "Bioprocess engineer review of scale-up criterion selection and descriptor trade-offs",
        "Evaluate trade-offs between preserving constant P/V, tip speed, and vvm/v_s for the organism's shear and oxygen sensitivity.",
    ),
    "VT-MEASURE-MIXING": (
        "measurement",
        "P2",
        "Characterize mixing time in target vessel (or review existing facility mixing study)",
        "Obtain or perform a tracer mixing-time (t_95) study in the target vessel at planned agitation speed to assess substrate/pH gradient risk.",
    ),
    "VT-MEASURE-VISCOSITY": (
        "measurement",
        "P2",
        "Measure broth density and dynamic viscosity at process conditions",
        "Measure end-of-batch broth density and viscosity (and shear-rate dependence if non-Newtonian) to replace assumed medium properties.",
    ),
    "VT-REVIEW-GEOMETRY": (
        "expert_review",
        "P2",
        "Review geometric and impeller differences between source and target vessels",
        "Assess hydrodynamic impact of differences in impeller type, impeller count, D/T, and H_L/T aspect ratio.",
    ),
    "VT-REVIEW-FORMULAS": (
        "expert_review",
        "P2",
        "Domain-expert sign-off on pending-review formulas and power-number assumptions",
        "Have the bioprocess scientific lead and advisor review ungassed power number N_p and pending engineering correlations.",
    ),
    "VT-DATA-COOLING": (
        "data_request",
        "P1",
        "Request target vessel cooling capacity specification from facility/vendor",
        "Obtain maximum jacket/coil heat removal rate (kW) at the target fermentation temperature and utility chilled-water supply temperature.",
    ),
    "VT-REVIEW-THERMAL": (
        "expert_review",
        "P1",
        "Perform metabolic + agitation heat balance against target cooling capability",
        "Calculate peak metabolic heat generation (from OUR or sugar consumption) plus mechanical agitation power against target cooling capacity.",
    ),
    "VT-REVIEW-EQUIPMENT": (
        "expert_review",
        "P1",
        "Resolve target vessel capability incompatibility",
        "Target operating point exceeds documented vessel limits; adjust working volume, modify scale-up criterion, or evaluate an alternative vessel.",
    ),
    "VT-DATA-VESSEL-SPEC": (
        "data_request",
        "P2",
        "Obtain missing vessel geometry and capability specifications",
        "Complete missing vessel profile fields from vendor engineering drawings or facility P&ID / datasheets.",
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
        "Inspect and document timestamp gaps, duplicate points, or out-of-range sensor readings in source batch exports.",
    ),
    "VT-DATA-CALIBRATION": (
        "data_request",
        "P3",
        "Document pre-run DO and pH probe calibration records",
        "Attach calibration logs confirming two-point pH and zero/100% DO calibration prior to inoculation.",
    ),
    "VT-DATA-REAL": (
        "experiment",
        "P1",
        "Replace synthetic/demo dataset with real laboratory fermentation batch data",
        "Import verified experimental batch exports from the laboratory bioreactor before making pilot transfer decisions.",
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
                    task_type=ttype,  # type: ignore[arg-type]
                    title=title,
                    description=desc,
                    priority=prio,  # type: ignore[arg-type]
                    triggered_by_rule_ids=[flag.rule_id],
                    triggered_by_check_ids=[],
                )
            else:
                existing = by_code[code]
                if flag.rule_id not in existing.triggered_by_rule_ids:
                    existing.triggered_by_rule_ids.append(flag.rule_id)
                if _PRIORITY_RANK[prio] < _PRIORITY_RANK[existing.priority]:
                    existing.priority = prio  # type: ignore[assignment]

    for chk in checks:
        if chk.outcome == "compatible":
            continue
        code = "VT-REVIEW-EQUIPMENT" if chk.outcome == "incompatible" else "VT-DATA-VESSEL-SPEC"
        if code in by_code and chk.check_id not in by_code[code].triggered_by_check_ids:
            by_code[code].triggered_by_check_ids.append(chk.check_id)

    return sorted(by_code.values(), key=lambda t: (_PRIORITY_RANK[t.priority], t.task_code))
