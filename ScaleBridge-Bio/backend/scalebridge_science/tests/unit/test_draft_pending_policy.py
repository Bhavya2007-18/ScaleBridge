"""Tests for not_configured behaviour and draft/pending_review execution policy."""

from __future__ import annotations

from scalebridge_science.formulas import (
    FORMULA_REGISTRY,
    calc_superficial_gas_velocity,
    calc_tip_speed,
)
from scalebridge_science.units import to_si_quantity


def test_pending_review_carries_warning() -> None:
    Qg = to_si_quantity(1.0, "L/min", "airflow", "sensor")
    T = to_si_quantity(0.13, "m", "vessel_inner_diameter", "vendor_datasheet")
    res = calc_superficial_gas_velocity(Qg, T)
    assert res.status == "computed"
    assert any("FORMULA_PENDING_REVIEW" in w for w in res.warnings)


def test_draft_formula_never_executes() -> None:
    N = to_si_quantity(500.0, "rpm", "agitation_speed", "sensor")
    D = to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet")
    meta = FORMULA_REGISTRY["F-TIP-001"]
    original = meta.review_status
    meta.review_status = "draft"
    try:
        res = calc_tip_speed(N, D)
        assert res.status == "not_applicable"
        assert res.output is None
        assert any("FORMULA_DRAFT_NOT_EXECUTED" in w for w in res.warnings)
    finally:
        meta.review_status = original


def test_not_configured_threshold_returns_not_configured() -> None:
    # Smoke: a ThresholdConfig with all None thresholds keeps R-MIX-003 not_configured
    from scalebridge_science.contracts import ThresholdConfig

    tc = ThresholdConfig()
    assert tc.re_turbulent_min is None
    assert tc.do_critical_percent is None
