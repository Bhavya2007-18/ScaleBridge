from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.report import ReportRow
from app.schemas.report import ReportRead
from app.services.report_service import ReportService

router = APIRouter()
report_svc = ReportService()

@router.post("/generate/{assessment_id}", response_model=ReportRead)
def generate_report(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        report = report_svc.generate_report(db, assessment_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{report_id}", response_model=ReportRead)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(ReportRow).filter(ReportRow.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
