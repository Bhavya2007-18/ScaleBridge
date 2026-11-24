import hashlib
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.assessment import Assessment
from app.models.report import ReportRow

class ReportService:
    """Generates structured audit-ready Process Transfer Reports."""

    def generate_report(self, db: Session, assessment_id: str, format_type: str = "json") -> ReportRow:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Compile sections
        sections = {
            "executive_summary": {
                "overall_readiness_score": assessment.overall_readiness_score,
                "status": assessment.status,
                "summary": assessment.summary_markdown
            },
            "engineering_calculations": [
                {
                    "criterion": c.criterion_name,
                    "parameter": c.output_parameter,
                    "value": c.value_numeric,
                    "unit": c.value_unit,
                    "provenance": c.provenance_classification,
                    "assumptions": c.assumptions
                } for c in assessment.calculations
            ],
            "risk_assessment": [
                {
                    "category": r.category,
                    "title": r.title,
                    "severity": r.severity,
                    "description": r.description,
                    "mitigation": r.mitigation_suggestion
                } for r in assessment.risks
            ],
            "equipment_compatibility": [
                {
                    "category": cp.item_category,
                    "parameter": cp.parameter_name,
                    "status": cp.status,
                    "required": cp.required_value,
                    "available": cp.available_value,
                    "unit": cp.unit,
                    "gap": cp.gap_analysis
                } for cp in assessment.compatibility_checks
            ],
            "validation_plan": [
                {
                    "phase": vt.phase,
                    "task": vt.task_name,
                    "description": vt.description,
                    "criteria": vt.success_criteria
                } for vt in assessment.validation_tasks
            ]
        }

        # Calculate cryptographic provenance hash
        hash_input = f"{assessment_id}:{assessment.overall_readiness_score}:{len(assessment.calculations)}"
        provenance_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        report_md = f"""# Process Transfer Report: Assessment {assessment_id[:8]}
**Overall Scale Readiness Score**: {assessment.overall_readiness_score:.1f}/100
**Status**: {assessment.status.upper()}
**Provenance Hash**: `{provenance_hash}`

## 1. Executive Summary
{assessment.summary_markdown}

## 2. Engineering Calculations
"""
        for c in assessment.calculations:
            report_md += f"- **{c.criterion_name}** ({c.output_parameter}): `{c.value_numeric} {c.value_unit}` [{c.provenance_classification.upper()}]\n"

        report_md += "\n## 3. Risk Register\n"
        for r in assessment.risks:
            report_md += f"- **[{r.severity.upper()}] {r.title}**: {r.description}\n  *Mitigation*: {r.mitigation_suggestion}\n"

        report_md += "\n## 4. Hardware Compatibility\n"
        for cp in assessment.compatibility_checks:
            report_md += f"- **{cp.parameter_name}**: `{cp.status.upper()}` (Required: {cp.required_value} {cp.unit}, Available: {cp.available_value} {cp.unit})\n"

        report_md += "\n## 5. Recommended Validation Plan\n"
        for vt in assessment.validation_tasks:
            report_md += f"- **[{vt.phase}] {vt.task_name}**: {vt.description} *(Criteria: {vt.success_criteria})*\n"

        report = ReportRow(
            assessment_id=assessment_id,
            format=format_type,
            title=f"Scale Transfer Assessment Report - {assessment_id[:8]}",
            summary_markdown=report_md,
            sections=sections,
            provenance_hash=provenance_hash
        )

        db.add(report)
        db.commit()
        db.refresh(report)
        return report
