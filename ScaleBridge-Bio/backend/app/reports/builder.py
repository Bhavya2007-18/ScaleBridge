from typing import Dict, Any
from app.models.report import ReportRow

class ReportBuilder:
    """Builds rendered PDF, HTML, or Markdown representations of Process Transfer Reports."""

    @staticmethod
    def to_markdown(report: ReportRow) -> str:
        return report.summary_markdown

    @staticmethod
    def to_json(report: ReportRow) -> Dict[str, Any]:
        return {
            "id": report.id,
            "assessment_id": report.assessment_id,
            "title": report.title,
            "provenance_hash": report.provenance_hash,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "sections": report.sections
        }
