"""Evidence-level derivation rules (docs/10_SCIENTIFIC_ENGINE.md §7)."""

from __future__ import annotations

from typing import Iterable
from scalebridge_science.contracts import EvidenceLevel, Quantity


def derive_evidence_level(inputs: Iterable[Quantity]) -> EvidenceLevel:
    """Return the weakest evidence level across all inputs of a calculation.

    Order of strength: measured > estimated > assumed > insufficient.
    """
    items = list(inputs)
    if not items:
        return "insufficient"

    natures = {q.value_nature for q in items}
    if "assumed" in natures:
        return "assumed"
    if "estimated" in natures:
        return "estimated"
    return "measured"


def derive_overall_evidence_level(levels: Iterable[EvidenceLevel]) -> EvidenceLevel:
    items = [lvl for lvl in levels if lvl != "insufficient"]
    if not items:
        return "insufficient"
    unique = set(items)
    if len(unique) == 1:
        return next(iter(unique))
    if "assumed" in unique:
        return "mixed"
    if "estimated" in unique and "measured" in unique:
        return "mixed"
    return "mixed"
