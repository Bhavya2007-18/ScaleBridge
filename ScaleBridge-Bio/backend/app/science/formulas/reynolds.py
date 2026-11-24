import math
from typing import Dict, Any

def calculate_reynolds_number(
    rpm: float,
    impeller_diameter_m: float,
    liquid_density_kg_m3: float = 1000.0,
    dynamic_viscosity_pa_s: float = 0.001
) -> Dict[str, Any]:
    """Calculates impeller mixing Reynolds number (Re = rho * N * D^2 / mu)."""
    if not all([rpm, impeller_diameter_m, liquid_density_kg_m3, dynamic_viscosity_pa_s]):
        return {
            "value": None,
            "unit": "dimensionless",
            "insufficient_evidence": True,
            "notes": "Missing required fluid dynamic physical properties"
        }
    n_rev_per_sec = rpm / 60.0
    re = (liquid_density_kg_m3 * n_rev_per_sec * (impeller_diameter_m ** 2)) / dynamic_viscosity_pa_s
    regime = "turbulent" if re > 10000 else "transitional" if re > 10 else "laminar"
    return {
        "value": round(re, 1),
        "regime": regime,
        "unit": "dimensionless",
        "insufficient_evidence": False,
        "assumptions": [
            f"Liquid density assumed {liquid_density_kg_m3} kg/m3",
            f"Dynamic viscosity assumed {dynamic_viscosity_pa_s} Pa.s (water equivalent)"
        ]
    }
