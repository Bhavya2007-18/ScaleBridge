"""Regression test reproducing the stored reference assessment."""

from __future__ import annotations

import json
import math
from pathlib import Path

from scalebridge_science.pipeline import run_assessment

from .reference_input import build_reference_input

STORED = Path(__file__).parent / "reference_assessments" / "reference_lab_to_pilot.json"


def _approx_equal(a: object, b: object, rel: float = 1e-12) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) or math.isnan(b):
            return a == b
        return math.isclose(a, b, rel_tol=rel, abs_tol=rel)
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_approx_equal(a[k], b[k], rel) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_approx_equal(x, y, rel) for x, y in zip(a, b))
    return a == b


def test_reference_assessment_reproduced() -> None:
    out = run_assessment(build_reference_input())
    payload = out.model_dump(mode="json")
    stored = json.loads(STORED.read_text(encoding="utf-8"))
    assert _approx_equal(payload, stored), "Reference assessment not reproduced within tolerance"
