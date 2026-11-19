from typing import Dict, Any

def calculate_otr(kla_per_h: float, c_star_mg_l: float, c_l_mg_l: float) -> Dict[str, Any]:
    """Calculates Oxygen Transfer Rate (OTR = kLa * (C* - CL)) in mmol/L/h or mg/L/h."""
    if kla_per_h is None or c_star_mg_l is None or c_l_mg_l is None:
        return {
            "value": None,
            "unit": "mg/L/h",
            "insufficient_evidence": True,
            "notes": "Missing kLa, saturation concentration, or dissolved oxygen liquid concentration"
        }
    delta_c = max(0.0, c_star_mg_l - c_l_mg_l)
    otr_mg_l_h = kla_per_h * delta_c
    otr_mmol_l_h = otr_mg_l_h / 32.0  # molecular weight O2 = 32 g/mol
    return {
        "value": round(otr_mg_l_h, 2),
        "value_mmol_l_h": round(otr_mmol_l_h, 2),
        "unit": "mg/L/h",
        "insufficient_evidence": False,
        "assumptions": ["Well-mixed bulk liquid phase with uniform driving force"]
    }
