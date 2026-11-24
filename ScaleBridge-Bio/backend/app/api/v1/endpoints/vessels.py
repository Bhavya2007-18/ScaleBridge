from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.tenant import Organization
from app.models.vessel import Vessel
from app.schemas.vessel import VesselCreate, VesselRead

router = APIRouter()

@router.get("/", response_model=List[VesselRead])
def list_vessels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Vessel).all()

@router.post("/", response_model=VesselRead)
def create_vessel(
    payload: VesselCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org = db.query(Organization).first()
    vessel = Vessel(
        tenant_id=org.id if org else "default",
        name=payload.name,
        facility=payload.facility,
        scale_category=payload.scale_category,
        working_volume_min_l=payload.working_volume_min_l,
        working_volume_max_l=payload.working_volume_max_l,
        total_volume_l=payload.total_volume_l,
        aspect_ratio=payload.aspect_ratio,
        impeller_count=payload.impeller_count,
        impeller_types=payload.impeller_types,
        baffle_count=payload.baffle_count,
        sparger_type=payload.sparger_type,
        max_rpm=payload.max_rpm,
        max_power_w=payload.max_power_w,
        max_gassing_vvm=payload.max_gassing_vvm
    )
    db.add(vessel)
    db.commit()
    db.refresh(vessel)
    return vessel

@router.get("/{vessel_id}", response_model=VesselRead)
def get_vessel(
    vessel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return vessel
