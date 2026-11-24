"""Risk-rule families (docs/12 §4).

Each module owns one rule family and exposes a pure function over a shared
``RuleContext``.  The aggregator below preserves the original public
``evaluate_risk_rules`` entry point and output ordering.
"""

from __future__ import annotations

from scalebridge_science.contracts import (
    AssessmentInput,
    CalculationResult,
    CompatibilityCheck,
    RiskFlag,
    TradeOffRow,
)
from scalebridge_science.readiness.registry import RuleContext, RuleMetadata
from scalebridge_science.readiness.rules.dat import evaluate_dat_rules
from scalebridge_science.readiness.rules.eqp import evaluate_eqp_rules
from scalebridge_science.readiness.rules.mix import evaluate_mix_rules
from scalebridge_science.readiness.rules.oxy import evaluate_oxy_rules
from scalebridge_science.readiness.rules.thm import evaluate_thm_rules


def evaluate_risk_rules(
    inp: AssessmentInput,
    calcs: list[CalculationResult],
    trade_offs: list[TradeOffRow],
    checks: list[CompatibilityCheck],
) -> list[RiskFlag]:
    """Evaluate every rule family in deterministic registry order."""
    ctx = RuleContext(
        inp=inp,
        calcs=calcs,
        trade_offs=trade_offs,
        checks=checks,
        thresholds=inp.scenario.thresholds,
    )
    flags: list[RiskFlag] = []
    flags.extend(evaluate_dat_rules(ctx))
    flags.extend(evaluate_oxy_rules(ctx))
    flags.extend(evaluate_mix_rules(ctx))
    flags.extend(evaluate_thm_rules(ctx))
    flags.extend(evaluate_eqp_rules(ctx))
    return flags


__all__ = [
    "RuleMetadata",
    "evaluate_dat_rules",
    "evaluate_eqp_rules",
    "evaluate_mix_rules",
    "evaluate_oxy_rules",
    "evaluate_risk_rules",
    "evaluate_thm_rules",
]
