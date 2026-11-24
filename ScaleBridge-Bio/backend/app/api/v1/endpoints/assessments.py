from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentRead
from app.services.assessment_service import AssessmentService

router = APIRouter()
assessment_svc = AssessmentService()

@router.post("/run/{scenario_id}", response_model=AssessmentRead)
def run_scaleup_assessment(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        assessment = assessment_svc.run_assessment(db, scenario_id)
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{assessment_id}", response_model=AssessmentRead)
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment
