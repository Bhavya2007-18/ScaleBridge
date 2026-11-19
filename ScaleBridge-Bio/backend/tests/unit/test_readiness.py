import pytest
from app.readiness.risk.engine import RiskEngine
from app.readiness.compatibility.engine import CompatibilityEngine
from app.readiness.validation.planner import ValidationPlanner

def test_risk_engine_shear_detection():
    engine = RiskEngine()
    metrics = {"tip_speed_m_s": 2.8, "kla_per_h": 45.0, "reynolds_number": 25000}
    flags = engine.evaluate(metrics, organism="CHO")
    
    # tip speed 2.8 > 2.2 threshold for CHO
    shear_flags = [f for f in flags if f.get("category") == "shear"]
    assert len(shear_flags) == 1
    assert shear_flags[0]["severity"] == "warning"

def test_compatibility_engine():
    engine = CompatibilityEngine()
    target_vessel = {"max_power_w": 500.0, "max_rpm": 200.0, "max_gassing_vvm": 1.0}
    operating_point = {"required_power_w": 750.0, "target_rpm": 150.0, "target_vvm": 0.8}
    
    checks = engine.evaluate(target_vessel, operating_point)
    power_check = next(c for c in checks if c["parameter_name"] == "motor_power")
    assert power_check["status"] == "incompatible"

def test_validation_planner():
    planner = ValidationPlanner()
    risk_flags = [{"category": "shear", "title": "Impeller Tip Speed Exceeds Shear Threshold"}]
    compat_checks = [{"parameter_name": "motor_power", "status": "incompatible", "gap_analysis": "Power shortfall"}]
    
    tasks = planner.generate_plan(risk_flags, compat_checks)
    assert len(tasks) >= 3  # Water run + shear assay + utility modification
