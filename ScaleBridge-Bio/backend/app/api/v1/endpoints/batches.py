from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.batch import Batch
from app.models.measurement import Measurement, QualityIssue
from app.schemas.batch import BatchCreate, BatchRead
from app.schemas.measurement import MeasurementRead, QualityIssueRead

router = APIRouter()

@router.get("/", response_model=List[BatchRead])
def list_batches(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Batch).filter(Batch.project_id == project_id).all()

@router.post("/", response_model=BatchRead)
def create_batch(
    project_id: str,
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = Batch(
        project_id=project_id,
        vessel_id=payload.vessel_id,
        batch_name=payload.batch_name,
        scale_type=payload.scale_type,
        metadata_json=payload.metadata_json
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

@router.get("/{batch_id}/measurements", response_model=List[MeasurementRead])
def get_batch_measurements(
    batch_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Measurement).filter(Measurement.batch_id == batch_id).limit(limit).all()

@router.get("/{batch_id}/issues", response_model=List[QualityIssueRead])
def get_batch_issues(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(QualityIssue).filter(QualityIssue.batch_id == batch_id).all()
