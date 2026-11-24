from typing import Dict, Any

def calculate_vvm(gas_flow_rate_slpm: float, working_volume_l: float) -> Dict[str, Any]:
    """Calculates volumetric gas flow rate in VVM (vol gas / vol liquid / min)."""
    if gas_flow_rate_slpm is None or working_volume_l is None or working_volume_l <= 0:
        return {
            "value": None,
            "unit": "vvm",
            "insufficient_evidence": True,
            "notes": "Missing gas flow or positive liquid volume"
        }
    vvm = gas_flow_rate_slpm / working_volume_l
    return {
        "value": round(vvm, 3),
        "unit": "vvm",
        "insufficient_evidence": False,
        "assumptions": ["Standard temperature and pressure flow normalization (SLPM)"]
    }
