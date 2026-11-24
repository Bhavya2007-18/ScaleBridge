"""Scale-up criteria and descriptor trade-off computation (docs/11 §8)."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel

from scalebridge_science.contracts import (
    AssessmentInput,
    CalculationResult,
    KlaEvidencePoint,
    Quantity,
    TradeOffRow,
)
from scalebridge_science.formulas import (
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
from scalebridge_science.criteria.registry import CRITERIA_REGISTRY, CriterionMetadata
from scalebridge_science.criteria.tradeoffs import (
    check_kla_mismatch_warnings,
    evaluate_criteria_and_calculations,
    find_kla_point,
)

__all__ = [
    "CRITERIA_REGISTRY",
    "CriterionMetadata",
    "check_kla_mismatch_warnings",
    "evaluate_criteria_and_calculations",
    "find_kla_point",
]
