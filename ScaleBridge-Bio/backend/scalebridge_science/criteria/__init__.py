"""Scale-up criteria and descriptor trade-off computation (docs/11 §8)."""

from __future__ import annotations

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
