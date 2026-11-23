"""Oxygen-transfer formulas (docs/11 §3)."""

from __future__ import annotations

from typing import Literal

from scalebridge_science.contracts import CalculationResult, Quantity
from scalebridge_science.formulas.registry import FORMULA_REGISTRY, run_formula


def calc_do_concentration(
    DO_pct: Quantity | None,
    C_star: Quantity | None,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
) -> CalculationResult:
    """F-DOC-001: ``C_L = (DO_% / 100) · C*``."""
    meta = FORMULA_REGISTRY["F-DOC-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    if DO_pct is not None:
        present["DO"] = DO_pct
    else:
        missing.append("DO (dissolved_oxygen % air saturation)")
    if C_star is not None:
        present["C_star"] = C_star
    else:
        missing.append("C* (oxygen_saturation_concentration)")

    def _compute() -> float:
        assert DO_pct is not None and C_star is not None
        return (DO_pct.value / 100.0) * C_star.value

    return run_formula(meta, scale, criterion_id, present, missing, _compute)


def calc_otr(
    kLa: Quantity | None,
    C_star: Quantity | None,
    C_L: Quantity | None,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
    extra_warnings: list[str] | None = None,
) -> CalculationResult:
    """F-OTR-001: ``OTR = kLa · (C* − C_L)``."""
    meta = FORMULA_REGISTRY["F-OTR-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    for key, label, q in [
        ("kLa", "kLa (volumetric mass-transfer coefficient)", kLa),
        ("C_star", "C* (oxygen_saturation_concentration)", C_star),
        ("C_L", "C_L (dissolved_oxygen_conc)", C_L),
    ]:
        if q is not None:
            present[key] = q
        else:
            missing.append(label)

    def _compute() -> float:
        assert kLa is not None and C_star is not None and C_L is not None
        return kLa.value * (C_star.value - C_L.value)

    return run_formula(
        meta,
        scale,
        criterion_id,
        present,
        missing,
        _compute,
        extra_warnings=extra_warnings,
    )


def calc_otr_max(
    kLa: Quantity | None,
    C_star: Quantity | None,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
    extra_warnings: list[str] | None = None,
) -> CalculationResult:
    """Upper bound of F-OTR-001 at ``C_L = 0``: ``OTR_max = kLa · C*``."""
    meta = FORMULA_REGISTRY["F-OTR-MAX"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    if kLa is not None:
        present["kLa"] = kLa
    else:
        missing.append("kLa (volumetric mass-transfer coefficient)")
    if C_star is not None:
        present["C_star"] = C_star
    else:
        missing.append("C* (oxygen_saturation_concentration)")

    def _compute() -> float:
        assert kLa is not None and C_star is not None
        return kLa.value * C_star.value

    return run_formula(
        meta,
        scale,
        criterion_id,
        present,
        missing,
        _compute,
        extra_warnings=extra_warnings,
    )


__all__ = ["calc_do_concentration", "calc_otr", "calc_otr_max"]
