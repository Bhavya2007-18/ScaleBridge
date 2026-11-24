from typing import Dict, Any, List

def evaluate_shear_risk(tip_speed_m_s: float, organism: str = "CHO") -> Dict[str, Any]:
    """Evaluates shear stress risk based on impeller tip speed and cellular morphology."""
    if tip_speed_m_s is None:
        return {
            "flag": False,
            "category": "shear",
            "severity": "unknown",
            "title": "Unquantified Shear Risk",
            "description": "Tip speed could not be computed; check impeller diameter and RPM data.",
            "mitigation": "Provide vessel geometry before proceeding to technical transfer."
        }
    
    threshold = 2.2 if "CHO" in organism or "mammalian" in organism.lower() else 4.5
    if tip_speed_m_s > threshold:
        return {
            "flag": True,
            "category": "shear",
            "severity": "critical" if tip_speed_m_s > (threshold * 1.3) else "warning",
            "title": "Impeller Tip Speed Exceeds Shear Threshold",
            "description": f"Target vessel tip speed of {tip_speed_m_s:.2f} m/s exceeds safe limit of {threshold} m/s for {organism}.",
            "mitigation": "Lower target agitation RPM or select a low-shear marine / pitched-blade impeller."
        }
    return {"flag": False}

def evaluate_mass_transfer_risk(kla_per_h: float, min_kla: float = 30.0) -> Dict[str, Any]:
    """Evaluates oxygenation/mass transfer limitation risk."""
    if kla_per_h is None:
        return {
            "flag": True,
            "category": "mass_transfer",
            "severity": "warning",
            "title": "Indeterminate Oxygen Transfer (kLa)",
            "description": "Target kLa was not calculated; risk of dissolved oxygen limitation.",
            "mitigation": "Conduct dynamic gassing-out characterization or input gassed power measurements."
        }
    if kla_per_h < min_kla:
        return {
            "flag": True,
            "category": "mass_transfer",
            "severity": "critical",
            "title": "Insufficient Oxygen Transfer Capacity",
            "description": f"Predicted target kLa of {kla_per_h:.1f} 1/h falls below required process baseline of {min_kla:.1f} 1/h.",
            "mitigation": "Increase sparging gas flow rate, enrich sparge gas with pure O2, or increase agitation rate."
        }
    return {"flag": False}

def evaluate_mixing_regime_risk(reynolds: float) -> Dict[str, Any]:
    """Evaluates turbulent vs laminar regime risks in industrial vessels."""
    if reynolds is not None and reynolds < 5000:
        return {
            "flag": True,
            "category": "mixing",
            "severity": "warning",
            "title": "Transitional or Incomplete Turbulent Mixing Regime",
            "description": f"Reynolds number ({reynolds:.0f}) suggests risk of stagnant zones or extended mixing time.",
            "mitigation": "Increase agitation rate or verify baffle configuration to prevent vortex formation."
        }
    return {"flag": False}
