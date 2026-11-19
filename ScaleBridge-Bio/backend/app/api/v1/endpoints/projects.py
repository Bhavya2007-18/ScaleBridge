from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project, PassportVersion
from app.models.tenant import Organization
from app.schemas.project import ProjectCreate, ProjectRead, PassportVersionRead

router = APIRouter()

@router.get("/", response_model=List[ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Project).all()

@router.post("/", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Default Biologics", slug="default-biologics")
        db.add(org)
        db.flush()

    project = Project(
        tenant_id=org.id,
        name=payload.name,
        description=payload.description,
        organism=payload.organism,
        target_molecule=payload.target_molecule,
        expression_system=payload.expression_system
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.get("/{project_id}/passport", response_model=List[PassportVersionRead])
def get_passports(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(PassportVersion).filter(PassportVersion.project_id == project_id).all()
