"""Domain C — Validation Planner (docs/14_VALIDATION_PLANNER.md)."""

from __future__ import annotations

from typing import Any

from scalebridge_science.contracts import CompatibilityCheck, RiskFlag, ValidationTaskSpec
from scalebridge_science.readiness.validation import (
    VALIDATION_TASK_TEMPLATES,
    generate_validation_tasks,
)


class ValidationPlanner:
    """Generates prioritized, evidence-linked experimental validation plans (VT-* registry)."""

    def generate_typed_tasks(
        self,
        flags: list[RiskFlag],
        checks: list[CompatibilityCheck],
    ) -> list[ValidationTaskSpec]:
        """Run canonical VT-* validation task planner with deduplication and priority escalation."""
        return generate_validation_tasks(flags, checks)

    def generate_plan(
        self,
        risk_flags: list[dict[str, Any]],
        compatibility_checks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate dictionary-formatted validation plan for lightweight readiness checks."""
        tasks: list[dict[str, Any]] = [
            {
                "task_code": "VT-MEASURE-MIXING",
                "phase": "pre_transfer",
                "task_name": "Hydrodynamic Characterization (Water Run)",
                "description": "Perform clean water mixing and power draw verification at target agitation and aeration rates.",
                "success_criteria": "Measured power draw and gas hold-up within +/- 10% of model prediction.",
                "risk_addressed": "Power curve discrepancies and motor overload",
            }
        ]

        for r in risk_flags:
            cat = r.get("category")
            if cat in ("shear", "mixing"):
                tasks.append(
                    {
                        "task_code": "VT-REVIEW-CRITERIA",
                        "phase": "lab_scale_down",
                        "task_name": "Scale-Down Shear Sensitivity Assay",
                        "description": "Subject seed culture in lab bioreactor or stirred rheometer to predicted maximum tip speed.",
                        "success_criteria": "Viability drop < 5% relative to standard control at harvest.",
                        "risk_addressed": r.get("title"),
                    }
                )
            elif cat in ("mass_transfer", "oxygen_transfer"):
                tasks.append(
                    {
                        "task_code": "VT-KLA-TARGET",
                        "phase": "pilot_qualification",
                        "task_name": "Dynamic kLa Measurement in Target Matrix",
                        "description": "Execute dynamic gassing-out test in target vessel using production medium formulation.",
                        "success_criteria": "kLa meets or exceeds minimum required transfer baseline.",
                        "risk_addressed": r.get("title"),
                    }
                )

        for c in compatibility_checks:
            if c.get("status") in ("incompatible", "cannot_evaluate"):
                tasks.append(
                    {
                        "task_code": "VT-REVIEW-EQUIPMENT",
                        "phase": "facility_fit_engineering",
                        "task_name": f"Utility Modification: {c.get('parameter_name')}",
                        "description": f"Address hardware gap: {c.get('gap_analysis')}",
                        "success_criteria": f"Vessel capability upgraded to meet requirement ({c.get('required_value')} {c.get('unit')}).",
                        "risk_addressed": f"Hardware Incompatibility in {c.get('item_category')}",
                    }
                )

        return tasks


__all__ = [
    "ValidationPlanner",
    "VALIDATION_TASK_TEMPLATES",
    "generate_validation_tasks",
]
