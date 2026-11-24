"""Hydrodynamic and geometric formulas (docs/11 §4, §4.5)."""

from __future__ import annotations

import math
from typing import Literal

from scalebridge_science.contracts import (
    CalculationResult,
    Provenance,
    Quantity,
    ValueNature,
)
from scalebridge_science.formulas.registry import FORMULA_REGISTRY, run_formula


def calc_tip_speed(
    N: Quantity | None,
    D: Quantity | None,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
) -> CalculationResult:
    """F-TIP-001: ``u_tip = π · N · D``."""
    meta = FORMULA_REGISTRY["F-TIP-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    if N is not None:
        present["N"] = N
    else:
        missing.append("N (agitation_speed)")
    if D is not None:
        present["D"] = D
    else:
        missing.append("D (impeller_diameter)")

    def _compute() -> float:
        assert N is not None and D is not None
        return math.pi * N.value * D.value

    return run_formula(meta, scale, criterion_id, present, missing, _compute)


def calc_reynolds(
    rho: Quantity | None,
    N: Quantity | None,
    D: Quantity | None,
    mu: Quantity | None,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
) -> CalculationResult:
    """F-RE-001: ``Re = ρ · N · D² / μ``."""
    meta = FORMULA_REGISTRY["F-RE-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    for key, label, q in [
        ("rho", "ρ (medium.density)", rho),
        ("N", "N (agitation_speed)", N),
        ("D", "D (impeller_diameter)", D),
        ("mu", "μ (medium.viscosity)", mu),
    ]:
        if q is not None:
            present[key] = q
        else:
            missing.append(label)

    def _compute() -> float:
        assert rho is not None and N is not None and D is not None and mu is not None
        return (rho.value * N.value * (D.value**2)) / mu.value

    return run_formula(
        meta,
        scale,
        criterion_id,
        present,
        missing,
        _compute,
        extra_warnings=["NEWTONIAN_ASSUMPTION: Calculated assuming Newtonian broth viscosity."],
    )


def calc_ungassed_power(
    N_p: Quantity | None,
    rho: Quantity | None,
    N: Quantity | None,
    D: Quantity | None,
    impeller_count: int | None = 1,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
) -> CalculationResult:
    """F-PWR-001: ``P₀ = n_imp · N_p · ρ · N³ · D⁵`` (ungassed estimate)."""
    meta = FORMULA_REGISTRY["F-PWR-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    for key, label, q in [
        ("N_p", "N_p (impeller_power_number)", N_p),
        ("rho", "ρ (medium.density)", rho),
        ("N", "N (agitation_speed)", N),
        ("D", "D (impeller_diameter)", D),
    ]:
        if q is not None:
            present[key] = q
        else:
            missing.append(label)

    n_imp = max(1, impeller_count or 1)
    present["n_imp"] = Quantity(
        value=float(n_imp),
        unit="dimensionless",
        original_value=float(n_imp),
        original_unit="dimensionless",
        display_value=float(n_imp),
        display_unit="dimensionless",
        provenance=Provenance.manual_entry,
        value_nature=ValueNature.measured,
    )

    def _compute() -> float:
        assert N_p is not None and rho is not None and N is not None and D is not None
        return float(n_imp) * N_p.value * rho.value * (N.value**3) * (D.value**5)

    res = run_formula(
        meta,
        scale,
        criterion_id,
        present,
        missing,
        _compute,
        extra_warnings=[
            "UNGASSED_POWER_ESTIMATE: Ungassed power P₀; gassed power reduction under aeration is not applied."
        ],
    )
    if res.output is not None:
        res.output.value_nature = ValueNature.estimated
        if res.evidence_level == "measured":
            res.evidence_level = "estimated"
    return res


def calc_power_per_volume(
    P: Quantity | None,
    V_w: Quantity | None,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
) -> CalculationResult:
    """F-PV-001: ``P/V = P / V_w``."""
    meta = FORMULA_REGISTRY["F-PV-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    if P is not None:
        present["P"] = P
    else:
        missing.append("P (power_draw or F-PWR-001)")
    if V_w is not None:
        present["V_w"] = V_w
    else:
        missing.append("V_w (working_volume)")

    def _compute() -> float:
        assert P is not None and V_w is not None
        return P.value / V_w.value

    return run_formula(meta, scale, criterion_id, present, missing, _compute)


def calc_d_over_t(
    D: Quantity | None,
    T: Quantity | None,
    scale: Literal["source", "target"] = "source",
) -> CalculationResult:
    """F-GEO-001: ``D/T = D / T``."""
    meta = FORMULA_REGISTRY["F-GEO-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    if D is not None:
        present["D"] = D
    else:
        missing.append("D (impeller_diameter)")
    if T is not None:
        present["T"] = T
    else:
        missing.append("T (vessel_inner_diameter)")

    def _compute() -> float:
        assert D is not None and T is not None
        return D.value / T.value

    return run_formula(meta, scale, None, present, missing, _compute)


def calc_hl_over_t(
    H_L: Quantity | None,
    T: Quantity | None,
    scale: Literal["source", "target"] = "source",
) -> CalculationResult:
    """F-GEO-002: ``H_L/T = H_L / T``."""
    meta = FORMULA_REGISTRY["F-GEO-002"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    if H_L is not None:
        present["H_L"] = H_L
    else:
        missing.append("H_L (liquid_height_at_working_volume)")
    if T is not None:
        present["T"] = T
    else:
        missing.append("T (vessel_inner_diameter)")

    def _compute() -> float:
        assert H_L is not None and T is not None
        return H_L.value / T.value

    return run_formula(meta, scale, None, present, missing, _compute)


__all__ = [
    "calc_d_over_t",
    "calc_hl_over_t",
    "calc_power_per_volume",
    "calc_reynolds",
    "calc_tip_speed",
    "calc_ungassed_power",
]
