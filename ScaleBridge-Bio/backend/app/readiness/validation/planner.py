from typing import Dict, Any, List

class ValidationPlanner:
    """Generates tiered risk-driven experimental validation plans."""

    def generate_plan(
        self,
        risk_flags: List[Dict[str, Any]],
        compatibility_checks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        tasks = []

        # Default sanity verification task
        tasks.append({
            "phase": "pre_transfer",
            "task_name": "Hydrodynamic Characterization (Water Run)",
            "description": "Perform clean water mixing and power draw verification at target agitation and aeration rates.",
            "success_criteria": "Measured power draw and gas hold-up within +/- 10% of model prediction.",
            "risk_addressed": "Power curve discrepancies and motor overload"
        })

        # Generate targeted tasks for detected risks
        for r in risk_flags:
            cat = r.get("category")
            if cat == "shear":
                tasks.append({
                    "phase": "lab_scale_down",
                    "task_name": "Scale-Down Shear Sensitivity Assay",
                    "description": "Subject seed culture in lab bioreactor or stirred rheometer to predicted maximum tip speed.",
                    "success_criteria": "Viability drop < 5% relative to standard control at harvest.",
                    "risk_addressed": r.get("title")
                })
            elif cat == "mass_transfer":
                tasks.append({
                    "phase": "pilot_qualification",
                    "task_name": "Dynamic kLa Measurement in Target Matrix",
                    "description": "Execute dynamic gassing-out test in target vessel using production medium formulation.",
                    "success_criteria": f"kLa meets or exceeds minimum required transfer baseline.",
                    "risk_addressed": r.get("title")
                })

        for c in compatibility_checks:
            if c.get("status") == "incompatible":
                tasks.append({
                    "phase": "facility_fit_engineering",
                    "task_name": f"Utility Modification: {c.get('parameter_name')}",
                    "description": f"Address hardware gap: {c.get('gap_analysis')}",
                    "success_criteria": f"Vessel capability upgraded to meet requirement ({c.get('required_value')} {c.get('unit')}).",
                    "risk_addressed": f"Hardware Incompatibility in {c.get('item_category')}"
                })

        return tasks
