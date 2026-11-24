from typing import Dict, Any, List

class CompatibilityEngine:
    """Checks vessel hardware and utility constraints against target process demands."""

    def evaluate(
        self,
        target_vessel: Dict[str, Any],
        predicted_operating_point: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        checks = []

        # 1. Agitation motor power check
        req_power_w = predicted_operating_point.get("required_power_w")
        avail_power_w = target_vessel.get("max_power_w")
        if req_power_w is not None and avail_power_w is not None:
            passed = req_power_w <= avail_power_w
            checks.append({
                "item_category": "agitation_motor",
                "parameter_name": "motor_power",
                "required_value": req_power_w,
                "available_value": avail_power_w,
                "unit": "W",
                "status": "compatible" if passed else "incompatible",
                "gap_analysis": None if passed else f"Motor power shortfall of {req_power_w - avail_power_w:.1f} W"
            })

        # 2. Maximum RPM check
        req_rpm = predicted_operating_point.get("target_rpm")
        max_rpm = target_vessel.get("max_rpm")
        if req_rpm is not None and max_rpm is not None:
            passed = req_rpm <= max_rpm
            checks.append({
                "item_category": "drive_assembly",
                "parameter_name": "agitator_speed",
                "required_value": req_rpm,
                "available_value": max_rpm,
                "unit": "rpm",
                "status": "compatible" if passed else "incompatible",
                "gap_analysis": None if passed else f"Required RPM ({req_rpm:.1f}) exceeds drive maximum ({max_rpm:.1f})"
            })

        # 3. Maximum aeration gas flow check
        req_vvm = predicted_operating_point.get("target_vvm")
        max_vvm = target_vessel.get("max_gassing_vvm")
        if req_vvm is not None and max_vvm is not None:
            passed = req_vvm <= max_vvm
            checks.append({
                "item_category": "mass_flow_controller",
                "parameter_name": "gas_flow_capacity",
                "required_value": req_vvm,
                "available_value": max_vvm,
                "unit": "vvm",
                "status": "compatible" if passed else "incompatible",
                "gap_analysis": None if passed else f"MFC capacity ({max_vvm:.2f} vvm) insufficient for demand ({req_vvm:.2f} vvm)"
            })

        return checks
