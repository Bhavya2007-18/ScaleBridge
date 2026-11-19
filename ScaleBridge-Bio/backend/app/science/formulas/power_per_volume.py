import math
from typing import Dict, Any

def calculate_power_per_volume(
    rpm: float,
    impeller_diameter_m: float,
    working_volume_m3: float,
    power_number_np: float = 5.0,
    density_kg_m3: float = 1000.0,
    gassed_factor: float = 0.8
) -> Dict[str, Any]:
    """Calculates power input per unit volume (P/V = Np * rho * N^3 * D^5 * gassed_factor / V)."""
    if not all([rpm, impeller_diameter_m, working_volume_m3]) or working_volume_m3 <= 0:
        return {
            "value": None,
            "unit": "W/m3",
            "insufficient_evidence": True,
            "notes": "Missing rpm, impeller diameter, or positive working volume"
        }
    n_rev_per_sec = rpm / 60.0
    ungassed_power = power_number_np * density_kg_m3 * (n_rev_per_sec ** 3) * (impeller_diameter_m ** 5)
    gassed_power = ungassed_power * gassed_factor
    p_per_v = gassed_power / working_volume_m3
    return {
        "value": round(p_per_v, 2),
        "total_power_w": round(gassed_power, 2),
        "unit": "W/m3",
        "insufficient_evidence": False,
        "assumptions": [
            f"Power number Np assumed {power_number_np}",
            f"Aerated power draw factor assumed {gassed_factor}",
            f"Density assumed {density_kg_m3} kg/m3"
        ]
    }
