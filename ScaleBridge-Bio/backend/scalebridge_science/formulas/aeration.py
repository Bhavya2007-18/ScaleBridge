"""Aeration formulas (docs/11 §5)."""

from __future__ import annotations

import math
from typing import Literal

from scalebridge_science.contracts import CalculationResult, Quantity
from scalebridge_science.formulas.registry import FORMULA_REGISTRY, run_formula


def calc_vvm(
    Q_g: Quantity | None,
    V_w: Quantity | None,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
) -> CalculationResult:
    """F-VVM-001: ``vvm = Q_g / V_w`` (1/s internally, displayed as 1/min)."""
    meta = FORMULA_REGISTRY["F-VVM-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    if Q_g is not None:
        present["Q_g"] = Q_g
    else:
        missing.append("Q_g (airflow / gas_flow)")
    if V_w is not None:
        present["V_w"] = V_w
    else:
        missing.append("V_w (working_volume)")

    def _compute() -> float:
        assert Q_g is not None and V_w is not None
        return Q_g.value / V_w.value

    return run_formula(meta, scale, criterion_id, present, missing, _compute)


def calc_superficial_gas_velocity(
    Q_g: Quantity | None,
    T: Quantity | None,
    scale: Literal["source", "target"] = "source",
    criterion_id: str | None = None,
) -> CalculationResult:
    """F-VS-001: ``v_s = Q_g / (π · T² / 4)``."""
    meta = FORMULA_REGISTRY["F-VS-001"]
    present: dict[str, Quantity] = {}
    missing: list[str] = []
    if Q_g is not None:
        present["Q_g"] = Q_g
    else:
        missing.append("Q_g (airflow / gas_flow)")
    if T is not None:
        present["T"] = T
    else:
        missing.append("T (vessel_inner_diameter)")

    def _compute() -> float:
        assert Q_g is not None and T is not None
        area = math.pi * (T.value**2) / 4.0
        return Q_g.value / area

    return run_formula(meta, scale, criterion_id, present, missing, _compute)


__all__ = ["calc_superficial_gas_velocity", "calc_vvm"]
