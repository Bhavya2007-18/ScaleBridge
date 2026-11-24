"""Hypothesis property tests for unit conversions and formula invariants."""

from __future__ import annotations

import math

from hypothesis import given
from hypothesis import strategies as st

from scalebridge_science.units import convert_value, to_si_quantity


@given(st.floats(min_value=0.1, max_value=1e4, allow_nan=False, allow_infinity=False))
def test_rpm_round_trip(rpm: float) -> None:
    si = to_si_quantity(rpm, "rpm", "agitation_speed")
    back = convert_value(si.value, "1 / second", "rpm")
    assert math.isclose(back, rpm, rel_tol=1e-9)


@given(st.floats(min_value=1.0, max_value=1e3, allow_nan=False, allow_infinity=False))
def test_rpm_to_rev_per_sec(rpm: float) -> None:
    q = to_si_quantity(rpm, "rpm", "agitation_speed")
    assert math.isclose(q.value, rpm / 60.0, rel_tol=1e-9)


@given(
    st.floats(min_value=0.1, max_value=1e3, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.1, max_value=1e3, allow_nan=False, allow_infinity=False),
)
def test_vvm_positive(qg_lpm: float, vw_l: float) -> None:
    qg = to_si_quantity(qg_lpm, "L/min", "airflow")
    vw = to_si_quantity(vw_l, "L", "working_volume")
    # vvm in 1/s = (L/min)/(L) converted
    vvm_si = qg.value / vw.value
    assert vvm_si > 0
    assert math.isfinite(vvm_si)


@given(st.floats(min_value=0.01, max_value=1e3, allow_nan=False, allow_infinity=False))
def test_convert_round_trip_meters(m: float) -> None:
    si = convert_value(m, "m", "meter")
    back = convert_value(si, "meter", "m")
    assert math.isclose(back, m, rel_tol=1e-9)
