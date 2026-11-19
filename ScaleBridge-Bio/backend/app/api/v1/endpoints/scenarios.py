from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioRead

router = APIRouter()

@router.get("/", response_model=List[ScenarioRead])
def list_scenarios(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Scenario).filter(Scenario.project_id == project_id).all()

@router.post("/", response_model=ScenarioRead)
def create_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    scenario = Scenario(
        project_id=payload.project_id,
        source_vessel_id=payload.source_vessel_id,
        target_vessel_id=payload.target_vessel_id,
        target_working_volume_l=payload.target_working_volume_l,
        selected_criteria=payload.selected_criteria,
        target_process_temperature_c=payload.target_process_temperature_c,
        operating_parameters=payload.operating_parameters,
        notes=payload.notes
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario

@router.get("/{scenario_id}", response_model=ScenarioRead)
def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario
