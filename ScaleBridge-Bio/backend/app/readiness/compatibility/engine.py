"""Domain C — Equipment Compatibility Engine (docs/13_EQUIPMENT_COMPATIBILITY.md)."""

from __future__ import annotations

from typing import Any

from scalebridge_science.contracts import AssessmentInput, CompatibilityCheck, TradeOffRow, VesselSpec
from scalebridge_science.readiness.compatibility import (
    REQUIRED_VESSEL_SPEC_KEYS,
    evaluate_compatibility_checks,
    inspect_missing_vessel_specs,
)


class CompatibilityEngine:
    """Checks vessel hardware and utility constraints against target process demands (C-* registry)."""

    def evaluate_typed(
        self,
        inp: AssessmentInput,
        trade_offs: list[TradeOffRow],
    ) -> list[CompatibilityCheck]:
        """Run canonical C-VOLUME-RANGE, C-AGIT-RANGE, C-MOTOR-POWER, C-GAS-RANGE, C-COOLING, C-TEMP-RANGE, C-INSTRUMENT checks."""
        return evaluate_compatibility_checks(inp, trade_offs)

    def inspect_missing_specs(self, vessel: VesselSpec) -> list[dict[str, object]]:
        """Return missing vessel specifications and downstream dependent formulas/checks."""
        return inspect_missing_vessel_specs(vessel)

    def evaluate(
        self,
        target_vessel: dict[str, Any],
        predicted_operating_point: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Evaluate dictionary-based vessel capability envelope against a predicted operating point."""
        checks: list[dict[str, Any]] = []

        # 1. Working volume range (C-VOLUME-RANGE)
        req_vol_l = predicted_operating_point.get("target_working_volume_l")
        min_vol_l = target_vessel.get("working_volume_min_l")
        max_vol_l = target_vessel.get("working_volume_max_l")
        if req_vol_l is not None and max_vol_l is not None:
            low_ok = min_vol_l is None or req_vol_l >= min_vol_l
            high_ok = req_vol_l <= max_vol_l
            passed = low_ok and high_ok
            checks.append(
                {
                    "check_id": "C-VOLUME-RANGE",
                    "item_category": "vessel_geometry",
                    "parameter_name": "working_volume",
                    "required_value": req_vol_l,
                    "available_value": max_vol_l,
                    "unit": "L",
                    "status": "compatible" if passed else "incompatible",
                    "gap_analysis": None
                    if passed
                    else f"Target volume ({req_vol_l:.1f} L) outside vessel working range [{min_vol_l or 0:.1f}, {max_vol_l:.1f}] L",
                }
            )

        # 2. Agitation motor power check (C-MOTOR-POWER)
        req_power_w = predicted_operating_point.get("required_power_w")
        avail_power_w = target_vessel.get("max_power_w")
        if req_power_w is not None and avail_power_w is not None:
            passed = req_power_w <= avail_power_w
            checks.append(
                {
                    "check_id": "C-MOTOR-POWER",
                    "item_category": "agitation_motor",
                    "parameter_name": "motor_power",
                    "required_value": req_power_w,
                    "available_value": avail_power_w,
                    "unit": "W",
                    "status": "compatible" if passed else "incompatible",
                    "gap_analysis": None
                    if passed
                    else f"Motor power shortfall of {req_power_w - avail_power_w:.1f} W",
                }
            )

        # 3. Maximum RPM check (C-AGIT-RANGE)
        req_rpm = predicted_operating_point.get("target_rpm")
        max_rpm = target_vessel.get("max_rpm")
        if req_rpm is not None and max_rpm is not None:
            passed = req_rpm <= max_rpm
            checks.append(
                {
                    "check_id": "C-AGIT-RANGE",
                    "item_category": "drive_assembly",
                    "parameter_name": "agitator_speed",
                    "required_value": req_rpm,
                    "available_value": max_rpm,
                    "unit": "rpm",
                    "status": "compatible" if passed else "incompatible",
                    "gap_analysis": None
                    if passed
                    else f"Required RPM ({req_rpm:.1f}) exceeds drive maximum ({max_rpm:.1f})",
                }
            )

        # 4. Maximum aeration gas flow check (C-GAS-RANGE)
        req_vvm = predicted_operating_point.get("target_vvm")
        max_vvm = target_vessel.get("max_gassing_vvm")
        if req_vvm is not None and max_vvm is not None:
            passed = req_vvm <= max_vvm
            checks.append(
                {
                    "check_id": "C-GAS-RANGE",
                    "item_category": "mass_flow_controller",
                    "parameter_name": "gas_flow_capacity",
                    "required_value": req_vvm,
                    "available_value": max_vvm,
                    "unit": "vvm",
                    "status": "compatible" if passed else "incompatible",
                    "gap_analysis": None
                    if passed
                    else f"MFC capacity ({max_vvm:.2f} vvm) insufficient for demand ({req_vvm:.2f} vvm)",
                }
            )

        return checks


__all__ = [
    "CompatibilityEngine",
    "REQUIRED_VESSEL_SPEC_KEYS",
    "evaluate_compatibility_checks",
    "inspect_missing_vessel_specs",
]
