import math
from typing import Dict, Any

def calculate_kla_van_riet(
    power_per_volume_w_m3: float,
    superficial_gas_velocity_m_s: float,
    alpha: float = 0.026,
    beta: float = 0.5,
    gamma: float = 0.5
) -> Dict[str, Any]:
    """Empirical Van't Riet correlation for kLa (s^-1) = alpha * (P/V)^beta * (v_s)^gamma."""
    if not power_per_volume_w_m3 or not superficial_gas_velocity_m_s:
        return {
            "value": None,
            "unit": "1/h",
            "insufficient_evidence": True,
            "notes": "Missing power per volume or superficial gas velocity"
        }
    kla_per_sec = alpha * (power_per_volume_w_m3 ** beta) * (superficial_gas_velocity_m_s ** gamma)
    kla_per_hour = kla_per_sec * 3600.0
    return {
        "value": round(kla_per_hour, 2),
        "unit": "1/h",
        "insufficient_evidence": False,
        "assumptions": [
            f"Van't Riet coefficients alpha={alpha}, beta={beta}, gamma={gamma} (coalescing air-water system)"
        ]
    }
