"""Pure unit tests for deterministic scale-up formulas (docs/11_SCALE_UP_CALCULATIONS.md)."""

from __future__ import annotations

import math

from scalebridge_science.formulas import (
    FORMULA_REGISTRY,
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
from scalebridge_science.units import to_si_quantity


def test_formula_registry_completeness() -> None:
    expected_formulas = [
        "F-TIP-001",
        "F-RE-001",
        "F-PV-001",
        "F-PWR-001",
        "F-VVM-001",
        "F-VS-001",
        "F-OTR-001",
        "F-DOC-001",
        "F-GEO-001",
        "F-GEO-002",
    ]
    for fid in expected_formulas:
        assert fid in FORMULA_REGISTRY, f"Missing registered formula: {fid}"
        meta = FORMULA_REGISTRY[fid]
        assert meta.formula_id == fid
        assert len(meta.required_inputs) > 0


def test_tip_speed_calculation() -> None:
    # 500 rpm (8.3333 1/s), D = 0.055 m -> u_tip = pi * 8.3333 * 0.055 = 1.4398966 m/s
    N = to_si_quantity(500.0, "rpm", "agitation_speed", "sensor")
    D = to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet")
    res = calc_tip_speed(N, D)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.value, 1.4398966, rel_tol=1e-5)
    assert res.evidence_level == "measured"


def test_tip_speed_missing_evidence() -> None:
    D = to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet")
    res = calc_tip_speed(None, D)
    assert res.status == "insufficient_evidence"
    assert res.output is None
    assert any("agitation_speed" in m for m in res.missing_inputs)


def test_reynolds_calculation() -> None:
    rho = to_si_quantity(1000.0, "kg/m^3", "density", "user_assumption")
    N = to_si_quantity(500.0, "rpm", "agitation_speed", "sensor")
    D = to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet")
    mu = to_si_quantity(0.001, "Pa*s", "viscosity", "user_assumption")
    res = calc_reynolds(rho, N, D, mu)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.value, 25208.3333, rel_tol=1e-5)


def test_reynolds_missing_viscosity() -> None:
    rho = to_si_quantity(1000.0, "kg/m^3", "density")
    N = to_si_quantity(500.0, "rpm", "agitation_speed")
    D = to_si_quantity(0.055, "m", "impeller_diameter")
    res = calc_reynolds(rho, N, D, None)
    assert res.status == "insufficient_evidence"
    assert res.output is None
    assert any("viscosity" in item for item in res.missing_inputs)


def test_power_per_volume() -> None:
    P = to_si_quantity(10.0, "W", "power_draw", "sensor")
    V = to_si_quantity(2.0, "L", "working_volume", "manual_entry")
    res = calc_power_per_volume(P, V)
    assert res.status == "computed"
    assert res.output is not None
    assert math.isclose(res.output.value, 5000.0, rel_tol=1e-6)


def test_ungassed_power_estimation() -> None:
    Np = to_si_quantity(5.0, "dimensionless", "impeller_power_number", "vendor_datasheet")
    rho = to_si_quantity(1000.0, "kg/m^3", "density", "manual_entry")
    N = to_si_quantity(500.0, "rpm", "agitation_speed", "sensor")
    D = to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet")
    res = calc_ungassed_power(Np, rho, N, D, impeller_count=2)
    assert res.status == "computed"
    assert res.output is not None
    # 2 impellers * 1.45626 W = 2.91252 W
    assert math.isclose(res.output.value, 2.91252, rel_tol=1e-4)
    assert res.output.value_nature == "estimated"


def test_vvm_and_superficial_velocity() -> None:
    Qg = to_si_quantity(1.0, "L/min", "airflow", "sensor")
    Vw = to_si_quantity(2.0, "L", "working_volume", "manual_entry")
    T = to_si_quantity(0.13, "m", "vessel_inner_diameter", "vendor_datasheet")

    res_vvm = calc_vvm(Qg, Vw)
    assert res_vvm.status == "computed"
    assert res_vvm.output is not None
    assert math.isclose(res_vvm.output.display_value or 0.0, 0.5, rel_tol=1e-6)

    res_vs = calc_superficial_gas_velocity(Qg, T)
    assert res_vs.status == "computed"
    assert res_vs.output is not None
    assert math.isclose(res_vs.output.value, 0.0012557, rel_tol=1e-4)


def test_otr_and_do_concentration() -> None:
    DO = to_si_quantity(30.0, "% air sat", "dissolved_oxygen", "sensor")
    C_star = to_si_quantity(0.20, "mmol/L", "oxygen_saturation_concentration", "user_assumption")
    kLa = to_si_quantity(100.0, "1/h", "kla", "lab_assay")

    doc = calc_do_concentration(DO, C_star)
    assert doc.status == "computed"
    assert doc.output is not None
    assert math.isclose(doc.output.display_value or 0.0, 0.06, rel_tol=1e-6)

    otr = calc_otr(kLa, C_star, doc.output)
    assert otr.status == "computed"
    assert otr.output is not None
    assert math.isclose(otr.output.display_value or 0.0, 14.0, rel_tol=1e-6)

    otr_max = calc_otr_max(kLa, C_star)
    assert otr_max.status == "computed"
    assert otr_max.output is not None
    assert math.isclose(otr_max.output.display_value or 0.0, 20.0, rel_tol=1e-6)


def test_geometric_ratios() -> None:
    D = to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet")
    T = to_si_quantity(0.13, "m", "vessel_inner_diameter", "vendor_datasheet")
    HL = to_si_quantity(0.15, "m", "liquid_height_at_working_volume", "manual_entry")

    d_t = calc_d_over_t(D, T)
    assert d_t.status == "computed"
    assert d_t.output is not None
    assert math.isclose(d_t.output.value, 0.055 / 0.13, rel_tol=1e-5)

    hl_t = calc_hl_over_t(HL, T)
    assert hl_t.status == "computed"
    assert hl_t.output is not None
    assert math.isclose(hl_t.output.value, 0.15 / 0.13, rel_tol=1e-5)
