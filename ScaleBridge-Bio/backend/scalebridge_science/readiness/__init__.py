"""Readiness layer: thresholds, equipment compatibility, risk rules and validation.

The implementation is split into focused modules (docs/10 §2):

* ``thresholds``    – explicitly supplied ``ThresholdConfig`` (no file/env I/O)
* ``compatibility`` – equipment capability checks (C-*)
* ``registry``      – versioned rule metadata and the shared ``RuleContext``
* ``rules``         – one module per rule family (R-DAT/OXY/MIX/THM/EQP)
* ``validation``    – gap-to-validation-task planner (VT-*)

The rule family modules are imported lazily so that ``contracts`` can import
``readiness.thresholds`` without creating an import cycle through ``criteria``
and ``formulas``.
"""

from __future__ import annotations

from typing import Any

from scalebridge_science.readiness.compatibility import (
    REQUIRED_VESSEL_SPEC_KEYS,
    evaluate_compatibility_checks,
    inspect_missing_vessel_specs,
)
from scalebridge_science.readiness.registry import (
    RULE_REGISTRY,
    RULE_REGISTRY_VERSION,
    RuleContext,
    RuleMetadata,
)
from scalebridge_science.readiness.thresholds import (
    DescriptorBand,
    SimilarityTolerance,
    ThresholdConfig,
)
from scalebridge_science.readiness.validation import (
    VALIDATION_TASK_TEMPLATES,
    generate_validation_tasks,
)

_LAZY_EXPORTS = {
    "evaluate_risk_rules": "scalebridge_science.readiness.rules",
    "evaluate_dat_rules": "scalebridge_science.readiness.rules",
    "evaluate_eqp_rules": "scalebridge_science.readiness.rules",
    "evaluate_mix_rules": "scalebridge_science.readiness.rules",
    "evaluate_oxy_rules": "scalebridge_science.readiness.rules",
    "evaluate_thm_rules": "scalebridge_science.readiness.rules",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "REQUIRED_VESSEL_SPEC_KEYS",
    "RULE_REGISTRY",
    "RULE_REGISTRY_VERSION",
    "VALIDATION_TASK_TEMPLATES",
    "DescriptorBand",
    "RuleContext",
    "RuleMetadata",
    "SimilarityTolerance",
    "ThresholdConfig",
    "evaluate_compatibility_checks",
    "evaluate_dat_rules",
    "evaluate_eqp_rules",
    "evaluate_mix_rules",
    "evaluate_oxy_rules",
    "evaluate_risk_rules",
    "evaluate_thm_rules",
    "generate_validation_tasks",
    "inspect_missing_vessel_specs",
]
