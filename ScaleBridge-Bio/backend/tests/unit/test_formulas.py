import pytest
import math
from app.science.formulas.tip_speed import calculate_tip_speed
from app.science.formulas.reynolds import calculate_reynolds_number
from app.science.formulas.power_per_volume import calculate_power_per_volume
from app.science.formulas.vvm import calculate_vvm
from app.science.formulas.kla import calculate_kla_van_riet
from app.science.formulas.otr import calculate_otr

def test_tip_speed_calculation():
    # 300 rpm, 0.1 m diameter -> pi * (300/60) * 0.1 = 1.5708 m/s
    res = calculate_tip_speed(300, 0.1)
    assert not res["insufficient_evidence"]
    assert pytest.approx(res["value"], rel=1e-3) == 1.5708

def test_tip_speed_missing_evidence():
    res = calculate_tip_speed(None, 0.1)
    assert res["insufficient_evidence"] is True
    assert res["value"] is None

def test_reynolds_number_turbulent():
    # Water at 20C, 300 rpm (5 rps), D=0.1m, rho=1000, mu=0.001
    # Re = 1000 * 5 * 0.01 / 0.001 = 50,000 (turbulent)
    res = calculate_reynolds_number(300, 0.1)
    assert not res["insufficient_evidence"]
    assert res["value"] == 50000.0
    assert res["regime"] == "turbulent"

def test_power_per_volume():
    # Np=5, rho=1000, N=5 rps (300 rpm), D=0.1m, gassed=0.8, V=0.005 m3 (5L)
    # Ungassed = 5 * 1000 * 125 * 0.00001 = 6.25 W
    # Gassed = 6.25 * 0.8 = 5.0 W
    # P/V = 5.0 / 0.005 = 1000 W/m3
    res = calculate_power_per_volume(300, 0.1, 0.005)
    assert not res["insufficient_evidence"]
    assert res["value"] == 1000.0
    assert res["total_power_w"] == 5.0

def test_vvm_calculation():
    res = calculate_vvm(2.5, 5.0)
    assert not res["insufficient_evidence"]
    assert res["value"] == 0.5
