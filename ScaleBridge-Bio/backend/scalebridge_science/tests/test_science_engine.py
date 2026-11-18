"""Unit, dimensional, and regression test suite for `scalebridge_science` (docs/11 §9, docs/18)."""

from __future__ import annotations

import math
import pytest

from scalebridge_science.contracts import (
    AssessmentInput,
    CriterionSelection,
    KlaEvidencePoint,
    MediumProperties,
    ProcessSummary,
    ScenarioConfig,
    ThresholdConfig,
    VesselSpec,
)
from scalebridge_science.formulas import (
    calc_do_concentration,
    calc_otr,
    calc_otr_max,
    calc_power_per_volume,
    calc_reynolds,
    calc_superficial_gas_velocity,
    calc_tip_speed,
    calc_ungassed_power,
    calc_vvm,
)
from scalebridge_science.pipeline import run_assessment
from scalebridge_science.units import (
    AmbiguousUnitError,
    UnitDimensionError,
    convert_value,
    to_si_quantity,
)


def test_t1_rpm_to_rev_per_sec_no_radian_error() -> None:
    """T1: 60 rpm must equal 1.0 1/s (revolutions per second, NOT 2*pi rad/s)."""
    q = to_si_quantity(60.0, "rpm", "agitation_speed", provenance="sensor")
    assert math.isclose(q.value, 1.0, rel_tol=1e-9)
    assert q.unit == "1 / second"
    assert math.isclose(q.display_value or 0.0, 60.0, rel_tol=1e-9)


def test_t2_impeller_tip_speed() -> None:
    """T2: F-TIP-001 with N = 500 rpm (8.333333 1/s), D = 0.055 m -> u_tip = 1.4398966 m/s."""
    N = to_si_quantity(500.0, "rpm", "agitation_speed", provenance="sensor")
    D = to_si_quantity(0.055, "m", "impeller_diameter", provenance="manual_entry")
    res = calc_tip_speed(N, D)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.value, 1.4398966, rel_tol=1e-5)
    assert res.evidence_level == "measured"


def test_t3_reynolds_number() -> None:
    """T3: F-RE-001 with rho=1000 kg/m3, N=500 rpm, D=0.055 m, mu=0.001 Pa*s -> Re = 25208.33."""
    rho = to_si_quantity(1000.0, "kg/m^3", "density", provenance="user_assumption")
    N = to_si_quantity(500.0, "rpm", "agitation_speed", provenance="sensor")
    D = to_si_quantity(0.055, "m", "impeller_diameter", provenance="manual_entry")
    mu = to_si_quantity(0.001, "Pa*s", "viscosity", provenance="user_assumption")
    res = calc_reynolds(rho, N, D, mu)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.value, 25208.3333, rel_tol=1e-5)
    assert res.evidence_level == "assumed"


def test_t4_vvm() -> None:
    """T4: F-VVM-001 with Q_g = 1 L/min, V_w = 2 L -> 0.5 vvm."""
    Q_g = to_si_quantity(1.0, "L/min", "airflow", provenance="sensor")
    V_w = to_si_quantity(2.0, "L", "working_volume", provenance="manual_entry")
    res = calc_vvm(Q_g, V_w)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.display_value or 0.0, 0.5, rel_tol=1e-6)


def test_t5_power_per_volume() -> None:
    """T5: F-PV-001 with P = 10 W, V_w = 2 L -> 5000 W/m3."""
    P = to_si_quantity(10.0, "W", "power_draw", provenance="sensor")
    V_w = to_si_quantity(2.0, "L", "working_volume", provenance="manual_entry")
    res = calc_power_per_volume(P, V_w)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.value, 5000.0, rel_tol=1e-6)


def test_t6_ungassed_power_from_power_number() -> None:
    """T6: F-PWR-001 with N_p=5, rho=1000, N=500 rpm, D=0.055 m -> P0 = 1.45626 W."""
    Np = to_si_quantity(5.0, "dimensionless", "impeller_power_number", provenance="vendor_datasheet")
    rho = to_si_quantity(1000.0, "kg/m^3", "density", provenance="manual_entry")
    N = to_si_quantity(500.0, "rpm", "agitation_speed", provenance="sensor")
    D = to_si_quantity(0.055, "m", "impeller_diameter", provenance="manual_entry")
    res = calc_ungassed_power(Np, rho, N, D, impeller_count=1)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.value, 1.45626, rel_tol=1e-4)
    assert res.output.value_nature == "estimated"


def test_t7_t8_otr_and_do_conversion() -> None:
    """T7 & T8: kLa=100 1/h, C*=0.20 mmol/L, DO=30% -> C_L=0.06 mmol/L, OTR=14.0 mmol/(L*h), OTR_max=20.0."""
    kLa = to_si_quantity(100.0, "1/h", "kla", provenance="lab_assay")
    C_star = to_si_quantity(0.20, "mmol/L", "oxygen_saturation_concentration", provenance="manual_entry")
    DO = to_si_quantity(30.0, "% air sat", "dissolved_oxygen", provenance="sensor")

    doc_res = calc_do_concentration(DO, C_star)
    assert doc_res.status == "computed"
    assert doc_res.output is not None
    assert math.isclose(doc_res.output.display_value or 0.0, 0.06, rel_tol=1e-6)

    otr_res = calc_otr(kLa, C_star, doc_res.output)
    assert otr_res.status == "computed"
    assert otr_res.output is not None
    assert math.isclose(otr_res.output.display_value or 0.0, 14.0, rel_tol=1e-6)

    otr_max_res = calc_otr_max(kLa, C_star)
    assert otr_max_res.status == "computed"
    assert otr_max_res.output is not None
    assert math.isclose(otr_max_res.output.display_value or 0.0, 20.0, rel_tol=1e-6)


def test_t9_superficial_gas_velocity() -> None:
    """T9: F-VS-001 with Q_g = 1 L/min, T = 0.13 m -> v_s = 1.2557e-3 m/s."""
    Q_g = to_si_quantity(1.0, "L/min", "airflow", provenance="sensor")
    T = to_si_quantity(0.13, "m", "vessel_inner_diameter", provenance="manual_entry")
    res = calc_superficial_gas_velocity(Q_g, T)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.value, 1.2557e-3, rel_tol=1e-4)


def test_t13_missing_input_returns_insufficient_evidence() -> None:
    """T13: F-RE-001 without viscosity returns insufficient_evidence and lists missing_inputs."""
    rho = to_si_quantity(1000.0, "kg/m^3", "density")
    N = to_si_quantity(500.0, "rpm", "agitation_speed")
    D = to_si_quantity(0.055, "m", "impeller_diameter")
    res = calc_reynolds(rho, N, D, None)
    assert res.status == "insufficient_evidence"
    assert res.output is None
    assert any("viscosity" in m for m in res.missing_inputs)


def test_t14_dimensional_error_and_ambiguous_percent() -> None:
    """T14: Passing volume unit 'L' for impeller diameter raises UnitDimensionError; bare '%' raises AmbiguousUnitError."""
    with pytest.raises(UnitDimensionError):
        to_si_quantity(2.0, "L", "impeller_diameter")
    with pytest.raises(AmbiguousUnitError):
        convert_value(50.0, "%", "percent_air_saturation")


def test_end_to_end_assessment_pipeline_and_determinism() -> None:
    """T10, T11, T12 & full pipeline determinism check."""
    src_vessel = VesselSpec(
        vessel_version_id="v-src-1",
        name="Lab-2L",
        scale_class="lab",
        impeller_type="rushton_turbine",
        impeller_count=1,
        sparger_type="ring",
        instrumentation=["ph_probe", "do_probe", "temperature_probe"],
        controls=["ph_control", "temperature_control", "do_cascade_agitation"],
        parameters={
            "working_volume_min": to_si_quantity(0.8, "L", "working_volume_min", "vendor_datasheet"),
            "working_volume_max": to_si_quantity(2.0, "L", "working_volume_max", "vendor_datasheet"),
            "vessel_inner_diameter": to_si_quantity(0.13, "m", "vessel_inner_diameter", "vendor_datasheet"),
            "liquid_height_at_working_volume": to_si_quantity(0.15, "m", "liquid_height_at_working_volume", "manual_entry"),
            "impeller_diameter": to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet"),
            "impeller_power_number": to_si_quantity(5.0, "dimensionless", "impeller_power_number", "vendor_datasheet"),
            "agitation_speed_min": to_si_quantity(100.0, "rpm", "agitation_speed_min", "vendor_datasheet"),
            "agitation_speed_max": to_si_quantity(1200.0, "rpm", "agitation_speed_max", "vendor_datasheet"),
        },
        kla_evidence=[
            KlaEvidencePoint(
                id="kla-src-1",
                kla=to_si_quantity(120.0, "1/h", "kla", "lab_assay"),
                agitation_speed=to_si_quantity(500.0, "rpm", "agitation_speed", "lab_assay"),
                gas_flow=to_si_quantity(1.0, "L/min", "airflow", "lab_assay"),
                working_volume=to_si_quantity(2.0, "L", "working_volume", "lab_assay"),
                medium_description="Defined medium",
            )
        ],
    )

    tgt_vessel = VesselSpec(
        vessel_version_id="v-tgt-1",
        name="Pilot-200L",
        scale_class="pilot",
        impeller_type="rushton_turbine",
        impeller_count=1,
        sparger_type="ring",
        instrumentation=["ph_probe", "do_probe", "temperature_probe"],
        controls=["ph_control", "temperature_control"],
        parameters={
            "working_volume_min": to_si_quantity(60.0, "L", "working_volume_min", "vendor_datasheet"),
            "working_volume_max": to_si_quantity(200.0, "L", "working_volume_max", "vendor_datasheet"),
            "vessel_inner_diameter": to_si_quantity(0.55, "m", "vessel_inner_diameter", "vendor_datasheet"),
            "liquid_height_at_working_volume": to_si_quantity(0.85, "m", "liquid_height_at_working_volume", "manual_entry"),
            "impeller_diameter": to_si_quantity(0.25, "m", "impeller_diameter", "vendor_datasheet"),
            "impeller_power_number": to_si_quantity(5.0, "dimensionless", "impeller_power_number", "vendor_datasheet"),
            "agitation_speed_min": to_si_quantity(50.0, "rpm", "agitation_speed_min", "vendor_datasheet"),
            "agitation_speed_max": to_si_quantity(400.0, "rpm", "agitation_speed_max", "vendor_datasheet"),
            "motor_power_limit": to_si_quantity(1500.0, "W", "motor_power_limit", "vendor_datasheet"),
            "gas_flow_min": to_si_quantity(10.0, "L/min", "gas_flow_min", "vendor_datasheet"),
            "gas_flow_max": to_si_quantity(200.0, "L/min", "gas_flow_max", "vendor_datasheet"),
        },
        kla_evidence=[],
    )

    proc = ProcessSummary(
        batch_ids=["batch-1"],
        operating={
            "agitation_speed": to_si_quantity(500.0, "rpm", "agitation_speed", "sensor"),
            "airflow": to_si_quantity(1.0, "L/min", "airflow", "sensor"),
            "working_volume": to_si_quantity(2.0, "L", "working_volume", "manual_entry"),
            "temperature": to_si_quantity(37.0, "degC", "temperature", "sensor"),
        },
        extremes={
            "do_min": to_si_quantity(18.0, "% air sat", "dissolved_oxygen", "sensor"),
            "our_max": to_si_quantity(25.0, "mmol/(L*h)", "our", "lab_assay"),
        },
    )

    med = MediumProperties(
        name="M9-mod",
        density=to_si_quantity(1000.0, "kg/m^3", "density", "user_assumption"),
        viscosity=to_si_quantity(0.001, "Pa*s", "viscosity", "user_assumption"),
        oxygen_saturation_concentration=to_si_quantity(
            0.20, "mmol/L", "oxygen_saturation_concentration", "user_assumption"
        ),
    )

    scen = ScenarioConfig(
        criteria=[
            CriterionSelection(criterion_id="S-PV", is_primary=True),
            CriterionSelection(criterion_id="S-TIP", is_primary=False),
            CriterionSelection(criterion_id="S-KLA", is_primary=False),
        ],
        aeration_basis="S-VVM",
        target_working_volume=to_si_quantity(150.0, "L", "working_volume", "manual_entry"),
        constraints={
            "min_do_required": to_si_quantity(20.0, "% air sat", "min_do_required", "user_assumption"),
            "max_tip_speed": to_si_quantity(2.0, "m/s", "max_tip_speed", "user_assumption"),
        },
        thresholds=ThresholdConfig(),
    )

    inp = AssessmentInput(
        source_vessel=src_vessel,
        target_vessel=tgt_vessel,
        process=proc,
        medium=med,
        scenario=scen,
        is_synthetic=True,
    )

    out1 = run_assessment(inp)
    out2 = run_assessment(inp)
    assert out1.model_dump() == out2.model_dump()

    # Check T10: S-TIP N_t = 500 * (0.055 / 0.25) = 110 rpm
    row_tip = next(r for r in out1.trade_offs if r.criterion_id == "S-TIP")
    assert math.isclose(row_tip.target_operating_point["N"].display_value or 0.0, 110.0, rel_tol=1e-5)

    # Check T11: S-PV N_t ≈ 169.1 rpm (2.818 1/s)
    row_pv = next(r for r in out1.trade_offs if r.criterion_id == "S-PV")
    assert math.isclose(row_pv.target_operating_point["N"].value, 2.818, rel_tol=1e-3)

    # Check T12: S-VVM Q_g,t = 0.5 vvm * 150 L = 75 L/min
    assert math.isclose(row_pv.target_operating_point["Q_g"].display_value or 0.0, 75.0, rel_tol=1e-5)

    # Verify expected flags triggered/insufficient
    rule_outcomes = {f.rule_id: f.outcome for f in out1.risk_flags}
    assert rule_outcomes["R-OXY-001"] == "triggered"  # do_min 18 < 20
    assert rule_outcomes["R-OXY-002"] == "insufficient_evidence"  # no target kLa
    assert rule_outcomes["R-MIX-001"] == "triggered"  # S-PV tip speed ~ 2.21 m/s > 2.0 m/s
    assert rule_outcomes["R-MIX-003"] == "not_configured"  # re_turbulent_min is None
    assert len(out1.validation_tasks) > 0
