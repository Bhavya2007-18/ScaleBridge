"""Metadata completeness and insufficient-evidence coverage for every registered formula."""

from __future__ import annotations

from scalebridge_science.formulas import FORMULA_REGISTRY, calc_d_over_t, calc_tip_speed
from scalebridge_science.units import to_si_quantity


def test_every_formula_has_required_metadata() -> None:
    required = {
        "formula_id",
        "version",
        "name",
        "equation_text",
        "equation_latex",
        "variables",
        "output",
        "source_basis",
        "blueprint_status",
        "review_status",
        "assumptions",
        "validity_limits",
        "required_inputs",
    }
    for fid, meta in FORMULA_REGISTRY.items():
        data = meta.model_dump()
        for field in required:
            assert field in data, f"{fid} missing metadata field {field}"
        assert data["equation_text"], f"{fid} has empty equation_text"
        assert data["assumptions"], f"{fid} has empty assumptions"
        assert data["required_inputs"], f"{fid} has empty required_inputs"
        assert meta.formula_id == fid


def test_tip_speed_insufficient_evidence() -> None:
    D = to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet")
    res = calc_tip_speed(None, D)
    assert res.status == "insufficient_evidence"
    assert res.output is None
    assert res.missing_inputs


def test_d_over_t_insufficient_evidence() -> None:
    D = to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet")
    res = calc_d_over_t(D, None)
    assert res.status == "insufficient_evidence"
    assert res.output is None
    assert res.missing_inputs
