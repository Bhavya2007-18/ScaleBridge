from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.scenario import Scenario
from app.models.vessel import Vessel
from app.models.assessment import (
    Assessment,
    CalculationResultRow,
    RiskFlagRow,
    CompatibilityCheckRow,
    ValidationTaskRow
)
from app.science.formulas.power_per_volume import calculate_power_per_volume
from app.science.formulas.tip_speed import calculate_tip_speed
from app.science.formulas.reynolds import calculate_reynolds_number
from app.science.formulas.vvm import calculate_vvm
from app.science.formulas.kla import calculate_kla_van_riet
from app.readiness.risk.engine import RiskEngine
from app.readiness.compatibility.engine import CompatibilityEngine
from app.readiness.validation.planner import ValidationPlanner

class AssessmentService:
    """Orchestrates end-to-end multi-criteria scale-up evaluations."""

    def __init__(self):
        self.risk_engine = RiskEngine()
        self.compatibility_engine = CompatibilityEngine()
        self.validation_planner = ValidationPlanner()

    def run_assessment(self, db: Session, scenario_id: str) -> Assessment:
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        source_vessel = db.query(Vessel).filter(Vessel.id == scenario.source_vessel_id).first()
        target_vessel = db.query(Vessel).filter(Vessel.id == scenario.target_vessel_id).first()

        # Target geometrical characteristics (estimated/fallback if not in parameters)
        t_vol_m3 = scenario.target_working_volume_l / 1000.0
        # Estimated diameter assuming H/T aspect ratio ~ 1.5
        t_diameter_m = (4.0 * t_vol_m3 / (3.14159 * 1.5)) ** (1.0 / 3.0)
        impeller_diameter_m = t_diameter_m * 0.35

        operating_params = scenario.operating_parameters or {}
        target_rpm = operating_params.get("agitation_rpm", 200.0)
        gas_flow_slpm = operating_params.get("gas_flow_slpm", scenario.target_working_volume_l * 0.5)

        # 1. Scientific Calculations
        tip_res = calculate_tip_speed(target_rpm, impeller_diameter_m)
        p_v_res = calculate_power_per_volume(target_rpm, impeller_diameter_m, t_vol_m3)
        re_res = calculate_reynolds_number(target_rpm, impeller_diameter_m)
        vvm_res = calculate_vvm(gas_flow_slpm, scenario.target_working_volume_l)

        # Superficial gas velocity: vs = (gas_flow_m3_s) / cross_sectional_area
        gas_flow_m3_s = (gas_flow_slpm / 60000.0)
        cross_section_m2 = 3.14159 * ((t_diameter_m / 2.0) ** 2)
        vs_m_s = gas_flow_m3_s / cross_section_m2 if cross_section_m2 > 0 else 0.01

        pv_val = p_v_res["value"] or 500.0
        kla_res = calculate_kla_van_riet(pv_val, vs_m_s)

        # 2. Risk Evaluation
        calculated_dict = {
            "tip_speed_m_s": tip_res["value"],
            "kla_per_h": kla_res["value"],
            "reynolds_number": re_res["value"],
            "power_per_volume_w_m3": pv_val
        }
        risks = self.risk_engine.evaluate(calculated_dict, organism="CHO")

        # 3. Hardware Compatibility
        target_vessel_dict = {
            "max_power_w": target_vessel.max_power_w if target_vessel else 5000.0,
            "max_rpm": target_vessel.max_rpm if target_vessel else 400.0,
            "max_gassing_vvm": target_vessel.max_gassing_vvm if target_vessel else 2.0
        }
        operating_point_dict = {
            "required_power_w": p_v_res.get("total_power_w", 1000.0),
            "target_rpm": target_rpm,
            "target_vvm": vvm_res["value"]
        }
        compatibilities = self.compatibility_engine.evaluate(target_vessel_dict, operating_point_dict)

        # 4. Validation Planning
        validation_tasks = self.validation_planner.generate_plan(risks, compatibilities)

        # Calculate overall readiness score (0 - 100)
        critical_risk_count = sum(1 for r in risks if r.get("severity") == "critical")
        warning_risk_count = sum(1 for r in risks if r.get("severity") == "warning")
        incompatible_count = sum(1 for c in compatibilities if c.get("status") == "incompatible")

        base_score = 100.0
        base_score -= (critical_risk_count * 25.0)
        base_score -= (warning_risk_count * 10.0)
        base_score -= (incompatible_count * 30.0)
        overall_score = max(0.0, min(100.0, base_score))

        # Save to DB
        assessment = Assessment(
            scenario_id=scenario_id,
            overall_readiness_score=overall_score,
            status="completed",
            summary_markdown=f"Scale-up assessment completed with readiness score of {overall_score:.1f}/100. "
                             f"Identified {len(risks)} risk flags and {len(validation_tasks)} validation milestones."
        )
        db.add(assessment)
        db.flush()

        # Add calculations
        calc_rows = [
            CalculationResultRow(
                assessment_id=assessment.id,
                criterion_name="Constant Power per Volume",
                output_parameter="power_per_volume",
                value_numeric=pv_val,
                value_unit="W/m3",
                provenance_classification="calculated",
                assumptions=p_v_res.get("assumptions", []),
                confidence_score=0.9
            ),
            CalculationResultRow(
                assessment_id=assessment.id,
                criterion_name="Impeller Dynamics",
                output_parameter="tip_speed",
                value_numeric=tip_res["value"],
                value_unit="m/s",
                provenance_classification="calculated",
                assumptions=tip_res.get("assumptions", []),
                confidence_score=0.95
            ),
            CalculationResultRow(
                assessment_id=assessment.id,
                criterion_name="Mass Transfer Prediction",
                output_parameter="kla",
                value_numeric=kla_res["value"],
                value_unit="1/h",
                provenance_classification="estimated",
                assumptions=kla_res.get("assumptions", []),
                confidence_score=0.8
            )
        ]
        db.add_all(calc_rows)

        # Add risk rows
        for r in risks:
            db.add(RiskFlagRow(
                assessment_id=assessment.id,
                category=r.get("category", "process"),
                title=r.get("title", "Risk"),
                description=r.get("description", ""),
                severity=r.get("severity", "warning"),
                mitigation_suggestion=r.get("mitigation", "")
            ))

        # Add compatibility rows
        for c in compatibilities:
            db.add(CompatibilityCheckRow(
                assessment_id=assessment.id,
                item_category=c.get("item_category", "vessel"),
                parameter_name=c.get("parameter_name", "parameter"),
                required_value=c.get("required_value"),
                available_value=c.get("available_value"),
                unit=c.get("unit"),
                status=c.get("status", "unknown"),
                gap_analysis=c.get("gap_analysis")
            ))

        # Add validation tasks
        for v in validation_tasks:
            db.add(ValidationTaskRow(
                assessment_id=assessment.id,
                phase=v.get("phase", "pre_transfer"),
                task_name=v.get("task_name", "Validation Step"),
                description=v.get("description", ""),
                success_criteria=v.get("success_criteria", ""),
                risk_addressed=v.get("risk_addressed")
            ))

        db.commit()
        db.refresh(assessment)
        return assessment
