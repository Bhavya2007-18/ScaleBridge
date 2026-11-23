"""Formula registry and deterministic formula implementations (docs/10, docs/11).

This module is an export surface only; implementations live in the sibling
modules.
"""

from __future__ import annotations

from scalebridge_science.formulas.aeration import calc_superficial_gas_velocity, calc_vvm
from scalebridge_science.formulas.hydrodynamics import (
    calc_d_over_t,
    calc_hl_over_t,
    calc_power_per_volume,
    calc_reynolds,
    calc_tip_speed,
    calc_ungassed_power,
)
from scalebridge_science.formulas.oxygen import calc_do_concentration, calc_otr, calc_otr_max
from scalebridge_science.formulas.registry import (
    FORMULA_REGISTRY,
    FORMULA_REGISTRY_VERSION,
    FormulaMetadata,
    run_formula,
)

__all__ = [
    "FORMULA_REGISTRY",
    "FORMULA_REGISTRY_VERSION",
    "FormulaMetadata",
    "calc_d_over_t",
    "calc_do_concentration",
    "calc_hl_over_t",
    "calc_otr",
    "calc_otr_max",
    "calc_power_per_volume",
    "calc_reynolds",
    "calc_superficial_gas_velocity",
    "calc_tip_speed",
    "calc_ungassed_power",
    "calc_vvm",
    "run_formula",
]
