from typing import Dict, Any, List
from app.readiness.risk.rules import (
    evaluate_shear_risk,
    evaluate_mass_transfer_risk,
    evaluate_mixing_regime_risk
)

class RiskEngine:
    """Evaluates multi-parametric scale-up risks across engineering disciplines."""

    def evaluate(
        self,
        calculated_metrics: Dict[str, Any],
        organism: str = "CHO"
    ) -> List[Dict[str, Any]]:
        flags = []
        
        tip_speed = calculated_metrics.get("tip_speed_m_s")
        shear_eval = evaluate_shear_risk(tip_speed, organism)
        if shear_eval.get("flag"):
            flags.append(shear_eval)

        kla = calculated_metrics.get("kla_per_h")
        kla_eval = evaluate_mass_transfer_risk(kla)
        if kla_eval.get("flag"):
            flags.append(kla_eval)

        re = calculated_metrics.get("reynolds_number")
        mix_eval = evaluate_mixing_regime_risk(re)
        if mix_eval.get("flag"):
            flags.append(mix_eval)

        return flags
