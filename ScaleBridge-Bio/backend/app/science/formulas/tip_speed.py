import math
from typing import Dict, Any

def calculate_tip_speed(rpm: float, impeller_diameter_m: float) -> Dict[str, Any]:
    """Calculates impeller tip speed (v_tip = pi * N * D)."""
    if rpm is None or impeller_diameter_m is None or impeller_diameter_m <= 0:
        return {
            "value": None,
            "unit": "m/s",
            "insufficient_evidence": True,
            "notes": "Missing rpm or positive impeller diameter"
        }
    n_rev_per_sec = rpm / 60.0
    tip_speed = math.pi * n_rev_per_sec * impeller_diameter_m
    return {
        "value": round(tip_speed, 4),
        "unit": "m/s",
        "insufficient_evidence": False,
        "assumptions": ["Impeller rotates at synchronous nominal motor frequency"]
    }
