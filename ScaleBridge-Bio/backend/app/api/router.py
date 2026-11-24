"""FastAPI router implementing all `/api/v1` endpoints specified in docs/08_API_SPECIFICATION.md."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
import io
import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import (
    ApiError,
    AuthContext,
    get_auth_context,
    get_current_user,
    record_audit,
    require_roles,
)
from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
)
from app.core.storage import object_store
from app.db.models import (
    Assessment,
    AuditEvent,
    Batch,
    CalculationResultRow,
    ColumnMapping,
    CompatibilityCheckRow,
    ConversionRecord,
    DataFile,
    Measurement,
    Membership,
    Organization,
    PassportVersion,
    Project,
    QualityIssue,
    RefreshToken,
    ReportRow,
    ReviewSignoff,
    RiskFlagRow,
    Scenario,
    User,
    ValidationTaskRow,
    Vessel,
    VesselParameter,
    VesselVersion,
)
from app.db.session import get_db
from app.modules.ingestion_service import (
    preview_file_bytes,
    read_dataframe_from_bytes,
    validate_and_normalize_dataframe,
)
from app.modules.report_service import render_transfer_report_pdf

from scalebridge_science.contracts import (
    AssessmentInput,
    CriterionSelection,
    KlaEvidencePoint,
    MediumProperties,
    MixingTimeEvidencePoint,
    ProcessSummary,
    Quantity,
    ScenarioConfig,
    ThresholdConfig,
    VesselSpec,
)
from scalebridge_science.criteria import CRITERIA_REGISTRY
from scalebridge_science.formulas import (
    FORMULA_REGISTRY,
    calc_d_over_t,
    calc_hl_over_t,
)
from scalebridge_science.pipeline import run_assessment
from scalebridge_science.readiness import RULE_REGISTRY, inspect_missing_vessel_specs
from scalebridge_science.units import (
    UnitDimensionError,
    VARIABLE_UNIT_SPECS,
    convert_value,
    to_si_quantity,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------
@router.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute( Organization.__table__.select().limit(1))
    return {"status": "ready"}


# ---------------------------------------------------------------------------
# 3.1 Auth & Identity
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        record_audit(db, None, None, "auth.login_failed", "user", req.email, {})
        db.commit()
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED, "UNAUTHENTICATED", "Invalid email or password"
        )

    user.last_login_at = datetime.now(timezone.utc)
    access_token, expires_in = create_access_token(user.id, user.email)
    raw_refresh, refresh_hash, refresh_exp = generate_refresh_token()

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_exp,
        )
    )
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    org_list = []
    for m in memberships:
        org = db.query(Organization).filter(Organization.id == m.organization_id).first()
        if org:
            org_list.append(
                {
                    "organization_id": org.id,
                    "name": org.name,
                    "slug": org.slug,
                    "role": m.role,
                }
            )

    record_audit(
        db,
        org_list[0]["organization_id"] if org_list else None,
        user.id,
        "auth.login",
        "user",
        user.id,
        {},
    )
    db.commit()

    response.set_cookie(
        key="sb_refresh_token",
        value=raw_refresh,
        httponly=True,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
    )
    return {
        "access_token": access_token,
        "expires_in": expires_in,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "memberships": org_list,
        },
    }


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    org_list = []
    for m in memberships:
        org = db.query(Organization).filter(Organization.id == m.organization_id).first()
        if org:
            org_list.append(
                {
                    "organization_id": org.id,
                    "name": org.name,
                    "slug": org.slug,
                    "role": m.role,
                }
            )
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "memberships": org_list,
    }


@router.get("/organizations/{org_id}/members")
def list_org_members(
    org_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if ctx.organization.id != org_id:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Organization not found")
    memberships = db.query(Membership).filter(Membership.organization_id == org_id).all()
    items = []
    for m in memberships:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            items.append(
                {
                    "user_id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "role": m.role,
                    "joined_at": m.created_at.isoformat(),
                }
            )
    return {"items": items}


# ---------------------------------------------------------------------------
# 3.2 Projects & Process Passport
# ---------------------------------------------------------------------------
class CreateProjectRequest(BaseModel):
    name: str
    product_family: str | None = "industrial_enzyme"
    organism_name: str | None = None
    strain_metadata: dict[str, Any] = Field(default_factory=dict)
    process_type: str = "fed_batch"
    is_synthetic_demo: bool = False


class CreatePassportVersionRequest(BaseModel):
    recipe_version: str = "v1.0"
    process_description: str | None = None
    organism_context: dict[str, Any] = Field(default_factory=dict)
    medium_context: dict[str, Any] = Field(default_factory=dict)
    process_parameters: list[dict[str, Any]] = Field(default_factory=list)
    material_context: dict[str, Any] = Field(default_factory=dict)
    change_note: str | None = "Updated Process Passport"


def _serialize_passport(pv: PassportVersion | None) -> dict[str, Any] | None:
    if pv is None:
        return None
    return {
        "id": pv.id,
        "project_id": pv.project_id,
        "version": pv.version,
        "recipe_version": pv.recipe_version,
        "process_description": pv.process_description,
        "organism_context": pv.organism_context,
        "medium_context": pv.medium_context,
        "process_parameters": pv.process_parameters,
        "material_context": pv.material_context,
        "change_note": pv.change_note,
        "created_by": pv.created_by,
        "created_at": pv.created_at.isoformat(),
    }


def _serialize_project(p: Project, db: Session) -> dict[str, Any]:
    latest_pv = (
        db.query(PassportVersion)
        .filter(PassportVersion.project_id == p.id)
        .order_by(PassportVersion.version.desc())
        .first()
    )
    batch_count = (
        db.query(Batch)
        .filter(Batch.project_id == p.id, Batch.archived_at.is_(None))
        .count()
    )
    scenario_count = db.query(Scenario).filter(Scenario.project_id == p.id).count()
    return {
        "id": p.id,
        "organization_id": p.organization_id,
        "name": p.name,
        "product_family": p.product_family,
        "organism_name": p.organism_name,
        "strain_metadata": p.strain_metadata,
        "process_type": p.process_type,
        "owner_user_id": p.owner_user_id,
        "is_synthetic_demo": p.is_synthetic_demo,
        "batch_count": batch_count,
        "scenario_count": scenario_count,
        "latest_passport": _serialize_passport(latest_pv),
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@router.get("/projects")
def list_projects(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    projects = (
        db.query(Project)
        .filter(
            Project.organization_id == ctx.organization.id,
            Project.archived_at.is_(None),
        )
        .order_by(Project.created_at.desc())
        .all()
    )
    return {"items": [_serialize_project(p, db) for p in projects], "next_cursor": None}


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    req: CreateProjectRequest,
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    existing = (
        db.query(Project)
        .filter(
            Project.organization_id == ctx.organization.id,
            Project.name == req.name.strip(),
        )
        .first()
    )
    if existing:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            f"Project '{req.name}' already exists in this organization",
        )
    proj = Project(
        organization_id=ctx.organization.id,
        name=req.name.strip(),
        product_family=req.product_family,
        organism_name=req.organism_name,
        strain_metadata=req.strain_metadata,
        process_type=req.process_type,
        owner_user_id=ctx.user.id,
        is_synthetic_demo=req.is_synthetic_demo,
    )
    db.add(proj)
    db.flush()

    pv = PassportVersion(
        organization_id=ctx.organization.id,
        project_id=proj.id,
        version=1,
        recipe_version="v1.0",
        process_description=f"Initial Process Passport for {proj.name}",
        organism_context={"organism_name": proj.organism_name, **proj.strain_metadata},
        medium_context={"name": "Standard Fermentation Medium"},
        process_parameters=[],
        material_context={},
        change_note="Initial passport created with project",
        created_by=ctx.user.id,
    )
    db.add(pv)
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "project.created",
        "project",
        proj.id,
        {"name": proj.name, "is_synthetic_demo": proj.is_synthetic_demo},
    )
    db.commit()
    db.refresh(proj)
    return _serialize_project(proj, db)


def _get_org_project(db: Session, org_id: str, project_id: str) -> Project:
    proj = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.organization_id == org_id,
            Project.archived_at.is_(None),
        )
        .first()
    )
    if not proj:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Project not found")
    return proj


@router.get("/projects/{project_id}")
def get_project(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    return _serialize_project(proj, db)


@router.get("/projects/{project_id}/passport-versions")
def list_passport_versions(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    versions = (
        db.query(PassportVersion)
        .filter(PassportVersion.project_id == proj.id)
        .order_by(PassportVersion.version.desc())
        .all()
    )
    return {"items": [_serialize_passport(v) for v in versions]}


@router.post("/projects/{project_id}/passport-versions", status_code=status.HTTP_201_CREATED)
def create_passport_version(
    project_id: str,
    req: CreatePassportVersionRequest,
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    latest = (
        db.query(PassportVersion)
        .filter(PassportVersion.project_id == proj.id)
        .order_by(PassportVersion.version.desc())
        .first()
    )
    next_ver = (latest.version + 1) if latest else 1

    # Validate any medium quantities if present
    med = dict(req.medium_context or {})
    for mkey in ("density", "viscosity", "oxygen_saturation_concentration"):
        mval = med.get(mkey)
        if isinstance(mval, dict) and mval.get("value") is not None and mval.get("unit"):
            try:
                q = to_si_quantity(
                    float(mval["value"]),
                    str(mval["unit"]),
                    mkey,
                    provenance=mval.get("provenance", "manual_entry"),
                    value_nature=mval.get("value_nature"),
                    source_ref=mval.get("source_ref"),
                )
                med[mkey] = q.model_dump()
            except UnitDimensionError as exc:
                raise ApiError(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "VALIDATION_ERROR",
                    str(exc),
                ) from exc

    pv = PassportVersion(
        organization_id=ctx.organization.id,
        project_id=proj.id,
        version=next_ver,
        recipe_version=req.recipe_version,
        process_description=req.process_description,
        organism_context=req.organism_context,
        medium_context=med,
        process_parameters=req.process_parameters,
        material_context=req.material_context,
        change_note=req.change_note,
        created_by=ctx.user.id,
    )
    proj.updated_at = datetime.now(timezone.utc)
    db.add(pv)
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "passport_version.created",
        "passport_version",
        pv.id,
        {"project_id": proj.id, "version": next_ver},
    )
    db.commit()
    db.refresh(pv)
    return _serialize_passport(pv) or {}


@router.get("/projects/{project_id}/data-checklist")
def get_project_data_checklist(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    latest_pv = (
        db.query(PassportVersion)
        .filter(PassportVersion.project_id == proj.id)
        .order_by(PassportVersion.version.desc())
        .first()
    )
    batches = (
        db.query(Batch)
        .filter(Batch.project_id == proj.id, Batch.archived_at.is_(None))
        .all()
    )
    vessels = (
        db.query(Vessel)
        .filter(
            Vessel.organization_id == ctx.organization.id,
            Vessel.archived_at.is_(None),
        )
        .all()
    )

    items: list[dict[str, Any]] = []
    med = (latest_pv.medium_context if latest_pv else {}) or {}

    def _med_status(k: str) -> str:
        obj = med.get(k)
        if not isinstance(obj, dict) or obj.get("value") is None:
            return "missing"
        return str(obj.get("value_nature") or "measured")

    items.append(
        {
            "key": "medium.density",
            "label": "Broth density (ρ)",
            "required_by": ["F-RE-001", "F-PWR-001", "S-PV"],
            "status": _med_status("density"),
        }
    )
    items.append(
        {
            "key": "medium.viscosity",
            "label": "Broth dynamic viscosity (μ)",
            "required_by": ["F-RE-001", "R-MIX-003"],
            "status": _med_status("viscosity"),
        }
    )
    items.append(
        {
            "key": "medium.oxygen_saturation_concentration",
            "label": "Oxygen saturation concentration (C*)",
            "required_by": ["F-DOC-001", "F-OTR-001", "F-OTR-MAX"],
            "status": _med_status("oxygen_saturation_concentration"),
        }
    )
    items.append(
        {
            "key": "batches.imported",
            "label": "Imported laboratory fermentation batch data (≥1 batch)",
            "required_by": ["F-TIP-001", "F-PV-001", "F-VVM-001", "R-OXY-001"],
            "status": "present" if len(batches) >= 1 else "missing",
        }
    )
    items.append(
        {
            "key": "batches.comparison_pair",
            "label": "At least 2 batches for batch-to-batch reproducibility comparison",
            "required_by": ["FR-DB-02"],
            "status": "present" if len(batches) >= 2 else "missing",
        }
    )
    items.append(
        {
            "key": "vessels.source_and_target",
            "label": "Source lab vessel and target pilot vessel profiles (≥2 vessels)",
            "required_by": ["S-PV", "S-TIP", "C-VOLUME-RANGE", "C-AGIT-RANGE"],
            "status": "present" if len(vessels) >= 2 else "missing",
        }
    )

    counts = {"present": 0, "measured": 0, "estimated": 0, "assumed": 0, "missing": 0}
    for it in items:
        st = it["status"]
        counts[st] = counts.get(st, 0) + 1

    return {"items": items, "summary": counts}


# ---------------------------------------------------------------------------
# 3.3 Files & Data Ingestion
# ---------------------------------------------------------------------------
@router.post("/projects/{project_id}/files", status_code=status.HTTP_201_CREATED)
async def upload_project_file(
    project_id: str,
    file: UploadFile = File(...),
    is_synthetic: bool = Form(default=False),
    source_description: str = Form(default="Laboratory controller CSV export"),
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    filename = file.filename or "upload.csv"
    if not (filename.lower().endswith(".csv") or filename.lower().endswith(".xlsx")):
        raise ApiError(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "UNSUPPORTED_FILE_TYPE",
            "Only .csv and .xlsx files are supported",
        )

    raw_bytes = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise ApiError(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "FILE_TOO_LARGE",
            f"File exceeds {settings.max_upload_mb} MB limit",
        )

    df_row = DataFile(
        organization_id=ctx.organization.id,
        project_id=proj.id,
        original_filename=filename,
        content_type=file.content_type or "text/csv",
        size_bytes=len(raw_bytes),
        sha256="",
        storage_key="",
        status="uploaded",
        is_synthetic=is_synthetic or proj.is_synthetic_demo,
        source_description=source_description,
        uploaded_by=ctx.user.id,
    )
    db.add(df_row)
    db.flush()

    storage_key = f"orgs/{ctx.organization.id}/raw/{df_row.id}/{filename}"
    sha256 = object_store.put_bytes(storage_key, raw_bytes, df_row.content_type)
    df_row.storage_key = storage_key
    df_row.sha256 = sha256

    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "file.uploaded",
        "data_file",
        df_row.id,
        {"filename": filename, "sha256": sha256, "size_bytes": len(raw_bytes)},
    )
    db.commit()
    db.refresh(df_row)
    return _serialize_datafile(df_row)


def _serialize_datafile(f: DataFile) -> dict[str, Any]:
    return {
        "id": f.id,
        "project_id": f.project_id,
        "original_filename": f.original_filename,
        "content_type": f.content_type,
        "size_bytes": f.size_bytes,
        "sha256": f.sha256,
        "status": f.status,
        "is_synthetic": f.is_synthetic,
        "source_description": f.source_description,
        "error_message": f.error_message,
        "last_quality_report": f.last_quality_report,
        "uploaded_by": f.uploaded_by,
        "uploaded_at": f.uploaded_at.isoformat(),
    }


def _get_org_file(db: Session, org_id: str, file_id: str) -> DataFile:
    f = (
        db.query(DataFile)
        .filter(DataFile.id == file_id, DataFile.organization_id == org_id)
        .first()
    )
    if not f:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Data file not found")
    return f


@router.get("/projects/{project_id}/files")
def list_project_files(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    files = (
        db.query(DataFile)
        .filter(DataFile.project_id == proj.id)
        .order_by(DataFile.uploaded_at.desc())
        .all()
    )
    return {"items": [_serialize_datafile(f) for f in files]}


@router.get("/files/{file_id}")
def get_datafile(
    file_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    f = _get_org_file(db, ctx.organization.id, file_id)
    return _serialize_datafile(f)


@router.get("/files/{file_id}/preview")
def preview_datafile(
    file_id: str,
    sheet: str | None = Query(default=None),
    rows: int = Query(default=25, ge=1, le=200),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    f = _get_org_file(db, ctx.organization.id, file_id)
    raw_bytes = object_store.get_bytes(f.storage_key)
    try:
        prev = preview_file_bytes(raw_bytes, f.original_filename, sheet_name=sheet, max_rows=rows)
    except Exception as exc:
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "INGESTION_ERROR", str(exc)
        ) from exc
    return prev


class SaveMappingRequest(BaseModel):
    mapping: dict[str, Any]
    save_as_template: bool = False
    template_name: str | None = None


@router.put("/files/{file_id}/mapping")
def save_file_mapping(
    file_id: str,
    req: SaveMappingRequest,
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    f = _get_org_file(db, ctx.organization.id, file_id)
    cm = ColumnMapping(
        organization_id=ctx.organization.id,
        data_file_id=f.id,
        name=req.template_name,
        is_template=req.save_as_template,
        mapping=req.mapping,
        created_by=ctx.user.id,
    )
    f.status = "mapped"
    db.add(cm)
    db.commit()
    return {"file_id": f.id, "status": f.status, "mapping_id": cm.id, "mapping": cm.mapping}


@router.post("/files/{file_id}/dry-run")
def dry_run_file(
    file_id: str,
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    f = _get_org_file(db, ctx.organization.id, file_id)
    cm = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.data_file_id == f.id)
        .order_by(ColumnMapping.created_at.desc())
        .first()
    )
    if not cm:
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INGESTION_ERROR",
            "Column mapping must be saved before running dry-run validation",
        )

    raw_bytes = object_store.get_bytes(f.storage_key)
    df, _ = read_dataframe_from_bytes(
        raw_bytes,
        f.original_filename,
        sheet_name=cm.mapping.get("sheet"),
        header_row=int(cm.mapping.get("header_row") or 1),
    )
    res = validate_and_normalize_dataframe(df, cm.mapping)
    report = {
        "file_id": f.id,
        "rows_total": res["rows_total"],
        "rows_imported": res["rows_imported"],
        "variables": res["variables"],
        "issues": res["issues"],
        "conversions": res["conversions"],
        "blocking": res["blocking"],
    }
    f.last_quality_report = report
    if not res["blocking"]:
        f.status = "validated"
    db.commit()
    return report


class CommitImportRequest(BaseModel):
    run_code: str
    scale_label: str | None = "2 L Lab"
    working_volume: float = 2.0
    working_volume_unit: str = "L"
    vessel_version_id: str | None = None
    passport_version_id: str | None = None
    operator: str | None = None
    notes: str | None = None


@router.post("/files/{file_id}/import", status_code=status.HTTP_201_CREATED)
def import_file_to_batch(
    file_id: str,
    req: CommitImportRequest,
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    f = _get_org_file(db, ctx.organization.id, file_id)
    cm = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.data_file_id == f.id)
        .order_by(ColumnMapping.created_at.desc())
        .first()
    )
    if not cm:
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INGESTION_ERROR",
            "Column mapping is missing for this file",
        )

    existing_batch = (
        db.query(Batch)
        .filter(Batch.project_id == f.project_id, Batch.run_code == req.run_code.strip())
        .first()
    )
    if existing_batch:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            f"Batch run_code '{req.run_code}' already exists in this project",
        )

    raw_bytes = object_store.get_bytes(f.storage_key)
    df, _ = read_dataframe_from_bytes(
        raw_bytes,
        f.original_filename,
        sheet_name=cm.mapping.get("sheet"),
        header_row=int(cm.mapping.get("header_row") or 1),
    )
    res = validate_and_normalize_dataframe(df, cm.mapping)
    if res["blocking"]:
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INGESTION_ERROR",
            "File has blocking data-quality or unit errors",
            details=res["issues"],
        )

    wv_qty = to_si_quantity(req.working_volume, req.working_volume_unit, "working_volume")

    batch = Batch(
        organization_id=ctx.organization.id,
        project_id=f.project_id,
        passport_version_id=req.passport_version_id,
        vessel_version_id=req.vessel_version_id,
        data_file_id=f.id,
        run_code=req.run_code.strip(),
        scale_label=req.scale_label,
        working_volume_original=req.working_volume,
        working_volume_unit=req.working_volume_unit,
        working_volume_si=wv_qty.value,
        start_time=res["start_time"],
        end_time=res["end_time"],
        operator=req.operator,
        notes=req.notes,
        is_synthetic=f.is_synthetic,
    )
    db.add(batch)
    db.flush()

    for m in res["normalized_measurements"]:
        db.add(
            Measurement(
                organization_id=ctx.organization.id,
                batch_id=batch.id,
                ts=m["ts"],
                elapsed_s=m["elapsed_s"],
                variable=m["variable"],
                value_original=m["value_original"],
                unit_original=m["unit_original"],
                value_si=m["value_si"],
                unit_si=m["unit_si"],
                provenance=m["provenance"],
                sensor_or_assay=m["sensor_or_assay"],
                calibration_status=m["calibration_status"],
                quality_flag=m["quality_flag"],
                data_file_id=f.id,
                source_row=m["source_row"],
            )
        )

    for conv in res["conversions"]:
        db.add(
            ConversionRecord(
                organization_id=ctx.organization.id,
                data_file_id=f.id,
                variable=conv["variable"],
                from_unit=conv["from_unit"],
                to_unit=conv["to_unit"],
                method=conv["method"],
                pint_version=conv["pint_version"],
            )
        )

    for iss in res["issues"]:
        db.add(
            QualityIssue(
                organization_id=ctx.organization.id,
                data_file_id=f.id,
                batch_id=batch.id,
                check_code=iss["check_code"],
                severity=iss["severity"],
                variable=iss["variable"],
                row_start=iss["row_start"],
                row_end=iss["row_end"],
                count=iss["count"],
                message=iss["message"],
            )
        )

    report = {
        "file_id": f.id,
        "rows_total": res["rows_total"],
        "rows_imported": res["rows_imported"],
        "variables": res["variables"],
        "issues": res["issues"],
        "conversions": res["conversions"],
        "blocking": False,
    }
    f.last_quality_report = report
    f.status = "imported"

    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "file.imported",
        "batch",
        batch.id,
        {"run_code": batch.run_code, "file_id": f.id, "rows": res["rows_imported"]},
    )
    db.commit()

    return {
        "batch_id": batch.id,
        "run_code": batch.run_code,
        "measurement_count": len(res["normalized_measurements"]),
        "quality_report": report,
    }


@router.get("/files/{file_id}/quality-report")
def get_file_quality_report(
    file_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    f = _get_org_file(db, ctx.organization.id, file_id)
    if not f.last_quality_report:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "No quality report available yet")
    return f.last_quality_report


# ---------------------------------------------------------------------------
# 3.4 Batches & Measurements
# ---------------------------------------------------------------------------
def _compute_batch_summary_dict(db: Session, batch: Batch) -> dict[str, Any]:
    rows = (
        db.query(Measurement)
        .filter(Measurement.batch_id == batch.id)
        .order_by(Measurement.elapsed_s.asc())
        .all()
    )
    by_var: dict[str, list[Measurement]] = {}
    for r in rows:
        by_var.setdefault(r.variable, []).append(r)

    var_stats: dict[str, Any] = {}
    for vkey, mlist in by_var.items():
        spec = VARIABLE_UNIT_SPECS.get(vkey, {"si": mlist[0].unit_si, "display": mlist[0].unit_original})
        unit_si = str(spec["si"])
        unit_disp = str(spec["display"])
        valid_si = [m.value_si for m in mlist if m.quality_flag == "ok" and m.value_si is not None]
        invalid_cnt = sum(1 for m in mlist if m.quality_flag == "invalid")
        missing_cnt = sum(1 for m in mlist if m.quality_flag == "missing")
        cal_st = mlist[0].calibration_status if mlist else "unknown"

        if valid_si:
            arr = np.array(valid_si, dtype=float)
            min_si = float(np.min(arr))
            p05_si = float(np.percentile(arr, 5))
            med_si = float(np.median(arr))
            p95_si = float(np.percentile(arr, 95))
            max_si = float(np.max(arr))
            mean_si = float(np.mean(arr))

            def _to_d(val: float) -> float:
                return convert_value(val, unit_si, unit_disp) if unit_si != unit_disp else val

            var_stats[vkey] = {
                "variable": vkey,
                "unit_si": unit_si,
                "unit_display": unit_disp,
                "count_total": len(mlist),
                "count_valid": len(valid_si),
                "count_invalid": invalid_cnt,
                "count_missing": missing_cnt,
                "calibration_status": cal_st,
                "min_si": min_si,
                "median_si": med_si,
                "max_si": max_si,
                "mean_si": mean_si,
                "min_display": _to_d(min_si),
                "p05_display": _to_d(p05_si),
                "median_display": _to_d(med_si),
                "p95_display": _to_d(p95_si),
                "max_display": _to_d(max_si),
                "mean_display": _to_d(mean_si),
            }
        else:
            var_stats[vkey] = {
                "variable": vkey,
                "unit_si": unit_si,
                "unit_display": unit_disp,
                "count_total": len(mlist),
                "count_valid": 0,
                "count_invalid": invalid_cnt,
                "count_missing": missing_cnt,
                "calibration_status": cal_st,
                "min_si": None,
                "median_si": None,
                "max_si": None,
                "mean_si": None,
                "min_display": None,
                "median_display": None,
                "max_display": None,
                "mean_display": None,
            }

    return {
        "batch_id": batch.id,
        "run_code": batch.run_code,
        "scale_label": batch.scale_label,
        "working_volume_original": batch.working_volume_original,
        "working_volume_unit": batch.working_volume_unit,
        "working_volume_si": batch.working_volume_si,
        "is_synthetic": batch.is_synthetic,
        "variables": var_stats,
    }


def _serialize_batch(b: Batch, db: Session) -> dict[str, Any]:
    summary = _compute_batch_summary_dict(db, b)
    return {
        "id": b.id,
        "project_id": b.project_id,
        "passport_version_id": b.passport_version_id,
        "vessel_version_id": b.vessel_version_id,
        "data_file_id": b.data_file_id,
        "run_code": b.run_code,
        "scale_label": b.scale_label,
        "working_volume_original": b.working_volume_original,
        "working_volume_unit": b.working_volume_unit,
        "working_volume_si": b.working_volume_si,
        "start_time": b.start_time.isoformat() if b.start_time else None,
        "end_time": b.end_time.isoformat() if b.end_time else None,
        "operator": b.operator,
        "notes": b.notes,
        "is_synthetic": b.is_synthetic,
        "variables_available": list(summary["variables"].keys()),
        "summary": summary["variables"],
        "created_at": b.created_at.isoformat(),
    }


@router.get("/projects/{project_id}/batches")
def list_project_batches(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    batches = (
        db.query(Batch)
        .filter(Batch.project_id == proj.id, Batch.archived_at.is_(None))
        .order_by(Batch.created_at.asc())
        .all()
    )
    return {"items": [_serialize_batch(b, db) for b in batches]}


def _get_org_batch(db: Session, org_id: str, batch_id: str) -> Batch:
    b = (
        db.query(Batch)
        .filter(
            Batch.id == batch_id,
            Batch.organization_id == org_id,
            Batch.archived_at.is_(None),
        )
        .first()
    )
    if not b:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Batch not found")
    return b


@router.get("/batches/{batch_id}")
def get_batch(
    batch_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    b = _get_org_batch(db, ctx.organization.id, batch_id)
    return _serialize_batch(b, db)


@router.get("/batches/{batch_id}/summary")
def get_batch_summary(
    batch_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    b = _get_org_batch(db, ctx.organization.id, batch_id)
    return _compute_batch_summary_dict(db, b)


@router.get("/batches/{batch_id}/measurements")
def get_batch_measurements(
    batch_id: str,
    variables: str | None = Query(default=None),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    b = _get_org_batch(db, ctx.organization.id, batch_id)
    q = db.query(Measurement).filter(Measurement.batch_id == b.id)
    if variables:
        var_list = [v.strip() for v in variables.split(",") if v.strip()]
        q = q.filter(Measurement.variable.in_(var_list))
    rows = q.order_by(Measurement.elapsed_s.asc()).all()

    series_by_var: dict[str, dict[str, Any]] = {}
    for r in rows:
        spec = VARIABLE_UNIT_SPECS.get(r.variable, {"si": r.unit_si, "display": r.unit_original})
        unit_si = str(spec["si"])
        unit_disp = str(spec["display"])
        if r.variable not in series_by_var:
            series_by_var[r.variable] = {
                "variable": r.variable,
                "unit_display": unit_disp,
                "unit_si": unit_si,
                "points": [],
            }
        val_disp: float | None = None
        if r.value_si is not None:
            val_disp = (
                convert_value(r.value_si, unit_si, unit_disp)
                if unit_si != unit_disp
                else r.value_si
            )
        series_by_var[r.variable]["points"].append(
            {
                "elapsed_s": r.elapsed_s,
                "elapsed_h": round(r.elapsed_s / 3600.0, 4),
                "value": val_disp,
                "value_si": r.value_si,
                "quality_flag": r.quality_flag,
            }
        )

    return {
        "batch_id": b.id,
        "run_code": b.run_code,
        "series": list(series_by_var.values()),
    }


# ---------------------------------------------------------------------------
# 3.5 Vessels
# ---------------------------------------------------------------------------
class VesselParamInput(BaseModel):
    key: str
    value: float
    unit: str
    provenance: str = "vendor_datasheet"
    value_nature: str | None = None
    source_ref: str | None = None
    note: str | None = None


class CreateVesselRequest(BaseModel):
    name: str
    scale_class: str = "lab"
    manufacturer: str | None = None
    model: str | None = None
    location: str | None = None
    impeller_type: str | None = "rushton_turbine"
    impeller_count: int | None = 1
    sparger_type: str | None = "ring"
    instrumentation: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    parameters: list[VesselParamInput] = Field(default_factory=list)
    kla_evidence: list[dict[str, Any]] = Field(default_factory=list)
    mixing_time_evidence: list[dict[str, Any]] = Field(default_factory=list)
    change_note: str | None = "Initial vessel profile"


class CreateVesselVersionRequest(BaseModel):
    impeller_type: str | None = "rushton_turbine"
    impeller_count: int | None = 1
    sparger_type: str | None = "ring"
    instrumentation: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    parameters: list[VesselParamInput] = Field(default_factory=list)
    kla_evidence: list[dict[str, Any]] = Field(default_factory=list)
    mixing_time_evidence: list[dict[str, Any]] = Field(default_factory=list)
    change_note: str | None = "Updated vessel profile version"


def _build_vessel_spec(vessel: Vessel, ver: VesselVersion, db: Session) -> VesselSpec:
    param_rows = (
        db.query(VesselParameter)
        .filter(VesselParameter.vessel_version_id == ver.id)
        .all()
    )
    param_map: dict[str, Quantity] = {}
    for pr in param_rows:
        spec = VARIABLE_UNIT_SPECS.get(pr.key, {"si": pr.unit_si, "display": pr.unit_original})
        disp_u = str(spec["display"])
        disp_v = (
            convert_value(pr.value_si, pr.unit_si, disp_u)
            if pr.unit_si != disp_u
            else pr.value_si
        )
        param_map[pr.key] = Quantity(
            value=pr.value_si,
            unit=pr.unit_si,
            original_value=pr.value_original,
            original_unit=pr.unit_original,
            display_value=disp_v,
            display_unit=disp_u,
            provenance=pr.provenance,  # type: ignore[arg-type]
            value_nature=pr.value_nature,  # type: ignore[arg-type]
            source_ref=pr.source_reference,
            note=pr.note,
        )

    kla_pts: list[KlaEvidencePoint] = []
    for kdict in ver.kla_evidence or []:
        try:
            kla_q = to_si_quantity(
                float(kdict["kla"]["value"]),
                str(kdict["kla"]["unit"]),
                "kla",
                provenance=kdict["kla"].get("provenance", "vendor_datasheet"),
                value_nature=kdict["kla"].get("value_nature"),
                source_ref=kdict["kla"].get("source_ref"),
            )
            n_q = (
                to_si_quantity(
                    float(kdict["agitation_speed"]["value"]),
                    str(kdict["agitation_speed"]["unit"]),
                    "agitation_speed",
                    provenance=kdict["agitation_speed"].get("provenance", "vendor_datasheet"),
                )
                if kdict.get("agitation_speed")
                else None
            )
            g_q = (
                to_si_quantity(
                    float(kdict["gas_flow"]["value"]),
                    str(kdict["gas_flow"]["unit"]),
                    "airflow",
                    provenance=kdict["gas_flow"].get("provenance", "vendor_datasheet"),
                )
                if kdict.get("gas_flow")
                else None
            )
            v_q = (
                to_si_quantity(
                    float(kdict["working_volume"]["value"]),
                    str(kdict["working_volume"]["unit"]),
                    "working_volume",
                    provenance=kdict["working_volume"].get("provenance", "vendor_datasheet"),
                )
                if kdict.get("working_volume")
                else None
            )
            kla_pts.append(
                KlaEvidencePoint(
                    id=str(kdict.get("id") or "kla-1"),
                    kla=kla_q,
                    agitation_speed=n_q,
                    gas_flow=g_q,
                    working_volume=v_q,
                    medium_description=kdict.get("medium_description"),
                    method=kdict.get("method"),
                )
            )
        except Exception:
            continue

    mix_pts: list[MixingTimeEvidencePoint] = []
    for mdict in ver.mixing_time_evidence or []:
        try:
            mt_q = to_si_quantity(
                float(mdict["mixing_time"]["value"]),
                str(mdict["mixing_time"]["unit"]),
                "mixing_time",
                provenance=mdict["mixing_time"].get("provenance", "vendor_datasheet"),
            )
            mix_pts.append(
                MixingTimeEvidencePoint(
                    id=str(mdict.get("id") or "mix-1"),
                    mixing_time=mt_q,
                    method=mdict.get("method"),
                )
            )
        except Exception:
            continue

    return VesselSpec(
        vessel_version_id=ver.id,
        name=vessel.name,
        scale_class=vessel.scale_class,  # type: ignore[arg-type]
        impeller_type=ver.impeller_type,
        impeller_count=ver.impeller_count,
        sparger_type=ver.sparger_type,
        instrumentation=ver.instrumentation or [],
        controls=ver.controls or [],
        parameters=param_map,
        kla_evidence=kla_pts,
        mixing_time_evidence=mix_pts,
    )


def _serialize_vessel(vessel: Vessel, ver: VesselVersion, db: Session) -> dict[str, Any]:
    spec = _build_vessel_spec(vessel, ver, db)
    missing_specs = inspect_missing_vessel_specs(spec)
    return {
        "id": vessel.id,
        "name": vessel.name,
        "scale_class": vessel.scale_class,
        "manufacturer": vessel.manufacturer,
        "model": vessel.model,
        "location": vessel.location,
        "latest_version": {
            "id": ver.id,
            "version": ver.version,
            "impeller_type": ver.impeller_type,
            "impeller_count": ver.impeller_count,
            "sparger_type": ver.sparger_type,
            "instrumentation": ver.instrumentation,
            "controls": ver.controls,
            "parameters": {k: v.model_dump() for k, v in spec.parameters.items()},
            "kla_evidence": [k.model_dump() for k in spec.kla_evidence],
            "mixing_time_evidence": [m.model_dump() for m in spec.mixing_time_evidence],
            "change_note": ver.change_note,
            "created_at": ver.created_at.isoformat(),
        },
        "missing_specifications": missing_specs,
        "created_at": vessel.created_at.isoformat(),
    }


def _persist_vessel_parameters(
    db: Session,
    org_id: str,
    vessel_version_id: str,
    params: list[VesselParamInput],
) -> None:
    for p in params:
        try:
            q = to_si_quantity(
                p.value,
                p.unit,
                p.key,
                provenance=p.provenance,  # type: ignore[arg-type]
                value_nature=p.value_nature,  # type: ignore[arg-type]
                source_ref=p.source_ref,
                note=p.note,
            )
        except UnitDimensionError as exc:
            raise ApiError(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", str(exc)
            ) from exc

        db.add(
            VesselParameter(
                organization_id=org_id,
                vessel_version_id=vessel_version_id,
                key=p.key,
                value_original=p.value,
                unit_original=p.unit,
                value_si=q.value,
                unit_si=q.unit,
                provenance=q.provenance,
                value_nature=q.value_nature,
                source_reference=p.source_ref,
                note=p.note,
            )
        )


@router.get("/vessels")
def list_vessels(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    vessels = (
        db.query(Vessel)
        .filter(
            Vessel.organization_id == ctx.organization.id,
            Vessel.archived_at.is_(None),
        )
        .order_by(Vessel.created_at.asc())
        .all()
    )
    items = []
    for v in vessels:
        ver = (
            db.query(VesselVersion)
            .filter(VesselVersion.vessel_id == v.id)
            .order_by(VesselVersion.version.desc())
            .first()
        )
        if ver:
            items.append(_serialize_vessel(v, ver, db))
    return {"items": items}


@router.post("/vessels", status_code=status.HTTP_201_CREATED)
def create_vessel(
    req: CreateVesselRequest,
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    existing = (
        db.query(Vessel)
        .filter(
            Vessel.organization_id == ctx.organization.id,
            Vessel.name == req.name.strip(),
        )
        .first()
    )
    if existing:
        raise ApiError(
            status.HTTP_409_CONFLICT, "CONFLICT", f"Vessel '{req.name}' already exists"
        )

    vessel = Vessel(
        organization_id=ctx.organization.id,
        name=req.name.strip(),
        scale_class=req.scale_class,
        manufacturer=req.manufacturer,
        model=req.model,
        location=req.location,
    )
    db.add(vessel)
    db.flush()

    ver = VesselVersion(
        organization_id=ctx.organization.id,
        vessel_id=vessel.id,
        version=1,
        impeller_type=req.impeller_type,
        impeller_count=req.impeller_count,
        sparger_type=req.sparger_type,
        instrumentation=req.instrumentation,
        controls=req.controls,
        kla_evidence=req.kla_evidence,
        mixing_time_evidence=req.mixing_time_evidence,
        change_note=req.change_note,
        created_by=ctx.user.id,
    )
    db.add(ver)
    db.flush()

    _persist_vessel_parameters(db, ctx.organization.id, ver.id, req.parameters)
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "vessel.created",
        "vessel",
        vessel.id,
        {"name": vessel.name, "scale_class": vessel.scale_class},
    )
    db.commit()
    return _serialize_vessel(vessel, ver, db)


@router.get("/vessels/compare")
def compare_vessels(
    a: str = Query(..., description="First vessel_version_id"),
    b: str = Query(..., description="Second vessel_version_id"),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ver_a = (
        db.query(VesselVersion)
        .filter(VesselVersion.id == a, VesselVersion.organization_id == ctx.organization.id)
        .first()
    )
    ver_b = (
        db.query(VesselVersion)
        .filter(VesselVersion.id == b, VesselVersion.organization_id == ctx.organization.id)
        .first()
    )
    if not ver_a or not ver_b:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Vessel version not found")

    ves_a = db.query(Vessel).filter(Vessel.id == ver_a.vessel_id, Vessel.organization_id == ctx.organization.id).first()
    ves_b = db.query(Vessel).filter(Vessel.id == ver_b.vessel_id, Vessel.organization_id == ctx.organization.id).first()
    if not ves_a or not ves_b:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Vessel not found")

    spec_a = _build_vessel_spec(ves_a, ver_a, db)
    spec_b = _build_vessel_spec(ves_b, ver_b, db)

    dt_a = calc_d_over_t(
        spec_a.parameters.get("impeller_diameter"),
        spec_a.parameters.get("vessel_inner_diameter"),
        "source",
    )
    hlt_a = calc_hl_over_t(
        spec_a.parameters.get("liquid_height_at_working_volume"),
        spec_a.parameters.get("vessel_inner_diameter"),
        "source",
    )
    dt_b = calc_d_over_t(
        spec_b.parameters.get("impeller_diameter"),
        spec_b.parameters.get("vessel_inner_diameter"),
        "target",
    )
    hlt_b = calc_hl_over_t(
        spec_b.parameters.get("liquid_height_at_working_volume"),
        spec_b.parameters.get("vessel_inner_diameter"),
        "target",
    )

    return {
        "vessel_a": _serialize_vessel(ves_a, ver_a, db),
        "vessel_b": _serialize_vessel(ves_b, ver_b, db),
        "geometric_ratios": {
            "vessel_a": {
                "D_over_T": dt_a.output.value if dt_a.output else None,
                "H_L_over_T": hlt_a.output.value if hlt_a.output else None,
            },
            "vessel_b": {
                "D_over_T": dt_b.output.value if dt_b.output else None,
                "H_L_over_T": hlt_b.output.value if hlt_b.output else None,
            },
        },
    }


@router.get("/vessels/{vessel_id}")
def get_vessel(
    vessel_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    vessel = (
        db.query(Vessel)
        .filter(Vessel.id == vessel_id, Vessel.organization_id == ctx.organization.id)
        .first()
    )
    if not vessel:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Vessel not found")
    ver = (
        db.query(VesselVersion)
        .filter(VesselVersion.vessel_id == vessel.id)
        .order_by(VesselVersion.version.desc())
        .first()
    )
    if ver is None:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Vessel version not found")
    return _serialize_vessel(vessel, ver, db)


@router.post("/vessels/{vessel_id}/versions", status_code=status.HTTP_201_CREATED)
def create_vessel_version(
    vessel_id: str,
    req: CreateVesselVersionRequest,
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    vessel = (
        db.query(Vessel)
        .filter(Vessel.id == vessel_id, Vessel.organization_id == ctx.organization.id)
        .first()
    )
    if not vessel:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Vessel not found")
    latest = (
        db.query(VesselVersion)
        .filter(VesselVersion.vessel_id == vessel.id)
        .order_by(VesselVersion.version.desc())
        .first()
    )
    next_ver = (latest.version + 1) if latest else 1

    ver = VesselVersion(
        organization_id=ctx.organization.id,
        vessel_id=vessel.id,
        version=next_ver,
        impeller_type=req.impeller_type,
        impeller_count=req.impeller_count,
        sparger_type=req.sparger_type,
        instrumentation=req.instrumentation,
        controls=req.controls,
        kla_evidence=req.kla_evidence,
        mixing_time_evidence=req.mixing_time_evidence,
        change_note=req.change_note,
        created_by=ctx.user.id,
    )
    db.add(ver)
    db.flush()
    _persist_vessel_parameters(db, ctx.organization.id, ver.id, req.parameters)
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "vessel_version.created",
        "vessel_version",
        ver.id,
        {"vessel_id": vessel.id, "version": next_ver},
    )
    db.commit()
    return _serialize_vessel(vessel, ver, db)


# ---------------------------------------------------------------------------
# 3.6 Scenarios, Assessments & Science Registries
# ---------------------------------------------------------------------------
class QuantityInputModel(BaseModel):
    value: float
    unit: str
    provenance: str = "user_assumption"
    value_nature: str | None = None
    source_ref: str | None = None
    note: str | None = None


class NamedQuantityInputModel(QuantityInputModel):
    key: str


class CreateScenarioRequest(BaseModel):
    name: str
    batch_ids: list[str]
    source_vessel_version_id: str
    target_vessel_version_id: str
    target_working_volume: QuantityInputModel
    criteria: list[CriterionSelection]
    aeration_basis: str = "S-VVM"
    kla_selection: dict[str, str | None] = Field(default_factory=dict)
    constraints: list[NamedQuantityInputModel] = Field(default_factory=list)
    assumptions: list[NamedQuantityInputModel] = Field(default_factory=list)
    thresholds: dict[str, Any] = Field(default_factory=dict)


def _serialize_scenario(s: Scenario, db: Session) -> dict[str, Any]:
    assessments = (
        db.query(Assessment)
        .filter(Assessment.scenario_id == s.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )
    return {
        "id": s.id,
        "project_id": s.project_id,
        "name": s.name,
        "batch_ids": s.batch_ids,
        "source_vessel_version_id": s.source_vessel_version_id,
        "target_vessel_version_id": s.target_vessel_version_id,
        "target_working_volume": {
            "value": s.target_working_volume_original,
            "unit": s.target_working_volume_unit,
            "value_si": s.target_working_volume_si,
        },
        "criteria": s.criteria,
        "aeration_basis": s.aeration_basis,
        "kla_selection": s.kla_selection,
        "constraints": s.constraints,
        "assumptions": s.assumptions,
        "thresholds": s.thresholds,
        "locked_at": s.locked_at.isoformat() if s.locked_at else None,
        "latest_assessment_id": assessments[0].id if assessments else None,
        "assessment_count": len(assessments),
        "created_at": s.created_at.isoformat(),
    }


@router.get("/projects/{project_id}/scenarios")
def list_project_scenarios(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    scenarios = (
        db.query(Scenario)
        .filter(Scenario.project_id == proj.id)
        .order_by(Scenario.created_at.desc())
        .all()
    )
    return {"items": [_serialize_scenario(s, db) for s in scenarios]}


@router.post("/projects/{project_id}/scenarios", status_code=status.HTTP_201_CREATED)
def create_scenario(
    project_id: str,
    req: CreateScenarioRequest,
    ctx: AuthContext = Depends(require_roles("scientist", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    proj = _get_org_project(db, ctx.organization.id, project_id)
    try:
        wv_q = to_si_quantity(
            req.target_working_volume.value,
            req.target_working_volume.unit,
            "working_volume",
            provenance=req.target_working_volume.provenance,  # type: ignore[arg-type]
            value_nature=req.target_working_volume.value_nature,  # type: ignore[arg-type]
        )
    except UnitDimensionError as exc:
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", str(exc)
        ) from exc

    scen = Scenario(
        organization_id=ctx.organization.id,
        project_id=proj.id,
        name=req.name.strip(),
        batch_ids=req.batch_ids,
        source_vessel_version_id=req.source_vessel_version_id,
        target_vessel_version_id=req.target_vessel_version_id,
        target_working_volume_original=req.target_working_volume.value,
        target_working_volume_unit=req.target_working_volume.unit,
        target_working_volume_si=wv_q.value,
        criteria=[c.model_dump() for c in req.criteria],
        aeration_basis=req.aeration_basis,
        kla_selection=req.kla_selection,
        constraints=[c.model_dump() for c in req.constraints],
        assumptions=[a.model_dump() for a in req.assumptions],
        thresholds=req.thresholds,
        created_by=ctx.user.id,
    )
    db.add(scen)
    db.flush()
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "scenario.created",
        "scenario",
        scen.id,
        {"name": scen.name, "project_id": proj.id},
    )
    db.commit()
    db.refresh(scen)
    return _serialize_scenario(scen, db)


@router.get("/scenarios/{scenario_id}")
def get_scenario(
    scenario_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    scen = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.organization_id == ctx.organization.id)
        .first()
    )
    if not scen:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Scenario not found")
    return _serialize_scenario(scen, db)


@router.post("/scenarios/{scenario_id}/assessments", status_code=status.HTTP_201_CREATED)
def execute_scenario_assessment(
    scenario_id: str,
    ctx: AuthContext = Depends(require_roles("scientist", "reviewer", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    scen = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.organization_id == ctx.organization.id)
        .first()
    )
    if not scen:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Scenario not found")

    proj = _get_org_project(db, ctx.organization.id, scen.project_id)
    latest_pv = (
        db.query(PassportVersion)
        .filter(PassportVersion.project_id == proj.id)
        .order_by(PassportVersion.version.desc())
        .first()
    )

    src_ver = (
        db.query(VesselVersion)
        .filter(
            VesselVersion.id == scen.source_vessel_version_id,
            VesselVersion.organization_id == ctx.organization.id,
        )
        .first()
    )
    tgt_ver = (
        db.query(VesselVersion)
        .filter(
            VesselVersion.id == scen.target_vessel_version_id,
            VesselVersion.organization_id == ctx.organization.id,
        )
        .first()
    )
    if not src_ver or not tgt_ver:
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Source or target vessel version not found",
        )

    src_vessel_row = db.query(Vessel).filter(Vessel.id == src_ver.vessel_id, Vessel.organization_id == ctx.organization.id).first()
    tgt_vessel_row = db.query(Vessel).filter(Vessel.id == tgt_ver.vessel_id, Vessel.organization_id == ctx.organization.id).first()
    if not src_vessel_row or not tgt_vessel_row:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Vessel not found")

    src_spec = _build_vessel_spec(src_vessel_row, src_ver, db)
    tgt_spec = _build_vessel_spec(tgt_vessel_row, tgt_ver, db)

    # Aggregate process summary across selected batches
    batches = (
        db.query(Batch)
        .filter(Batch.id.in_(scen.batch_ids), Batch.organization_id == ctx.organization.id)
        .all()
        if scen.batch_ids
        else []
    )
    is_syn = proj.is_synthetic_demo or any(b.is_synthetic for b in batches)

    operating_map: dict[str, Quantity] = {}
    extremes_map: dict[str, Quantity] = {}
    cal_map: dict[str, str] = {}
    high_dq_vars: set[str] = set()

    if batches:
        summaries = [_compute_batch_summary_dict(db, b) for b in batches]
        # Working volume from batch metadata
        wv_vals = [b.working_volume_si for b in batches if b.working_volume_si is not None]
        if wv_vals:
            max_wv_si = float(max(wv_vals))
            operating_map["working_volume"] = Quantity(
                value=max_wv_si,
                unit="m**3",
                original_value=convert_value(max_wv_si, "m**3", "L"),
                original_unit="L",
                display_value=convert_value(max_wv_si, "m**3", "L"),
                display_unit="L",
                provenance="manual_entry",
                value_nature="measured",
                source_ref="batch_metadata:working_volume",
            )

        for vkey in ("agitation_speed", "airflow", "gas_flow_total", "temperature", "power_draw", "ph", "dissolved_oxygen"):
            meds = [
                s["variables"][vkey]["median_si"]
                for s in summaries
                if vkey in s["variables"] and s["variables"][vkey]["median_si"] is not None
            ]
            if meds:
                # Take the most demanding (max) across selected batches
                chosen_si = float(max(meds))
                spec = VARIABLE_UNIT_SPECS[vkey]
                u_si = str(spec["si"])
                u_disp = str(spec["display"])
                disp_v = convert_value(chosen_si, u_si, u_disp) if u_si != u_disp else chosen_si
                operating_map[vkey] = Quantity(
                    value=chosen_si,
                    unit=u_si,
                    original_value=disp_v,
                    original_unit=u_disp,
                    display_value=disp_v,
                    display_unit=u_disp,
                    provenance="sensor",
                    value_nature="measured",
                    source_ref=f"batch_summary:{vkey}:median",
                )
            for s in summaries:
                if vkey in s["variables"]:
                    cal_map[vkey] = s["variables"][vkey]["calibration_status"]

        # DO min
        do_mins = [
            s["variables"]["dissolved_oxygen"]["min_si"]
            for s in summaries
            if "dissolved_oxygen" in s["variables"]
            and s["variables"]["dissolved_oxygen"]["min_si"] is not None
        ]
        if do_mins:
            min_do_val = float(min(do_mins))
            extremes_map["do_min"] = Quantity(
                value=min_do_val,
                unit="percent_air_saturation",
                original_value=min_do_val,
                original_unit="% air sat",
                display_value=min_do_val,
                display_unit="% air sat",
                provenance="sensor",
                value_nature="measured",
                source_ref="batch_summary:dissolved_oxygen:min",
            )

        # OUR max
        our_maxs = [
            s["variables"]["our"]["max_si"]
            for s in summaries
            if "our" in s["variables"] and s["variables"]["our"]["max_si"] is not None
        ]
        if our_maxs:
            max_our_si = float(max(our_maxs))
            disp_our = convert_value(max_our_si, "mol / (m**3 * second)", "mmol/(L*h)")
            extremes_map["our_max"] = Quantity(
                value=max_our_si,
                unit="mol / (m**3 * second)",
                original_value=disp_our,
                original_unit="mmol/(L*h)",
                display_value=disp_our,
                display_unit="mmol/(L*h)",
                provenance="lab_assay",
                value_nature="measured",
                source_ref="batch_summary:our:max",
            )

        # High severity DQ issues
        q_issues = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.batch_id.in_([b.id for b in batches]),
                QualityIssue.severity.in_(["high", "critical"]),
            )
            .all()
        )
        for qi in q_issues:
            if qi.variable:
                high_dq_vars.add(qi.variable)

    # Medium properties from Passport + Scenario assumptions override
    med_ctx = (latest_pv.medium_context if latest_pv else {}) or {}
    med_quantities: dict[str, Quantity | None] = {
        "density": None,
        "viscosity": None,
        "oxygen_saturation_concentration": None,
    }
    for mkey in list(med_quantities.keys()):
        mobj = med_ctx.get(mkey)
        if isinstance(mobj, dict) and mobj.get("value") is not None:
            try:
                med_quantities[mkey] = to_si_quantity(
                    float(mobj.get("original_value") or mobj["value"]),
                    str(mobj.get("original_unit") or mobj["unit"]),
                    mkey,
                    provenance=mobj.get("provenance", "manual_entry"),
                    value_nature=mobj.get("value_nature"),
                )
            except Exception:
                pass

    for assump in scen.assumptions or []:
        akey = str(assump.get("key") or "").replace("medium.", "")
        if akey in med_quantities and assump.get("value") is not None:
            med_quantities[akey] = to_si_quantity(
                float(assump["value"]),
                str(assump["unit"]),
                akey,
                provenance=assump.get("provenance", "user_assumption"),
                value_nature=assump.get("value_nature", "assumed"),
                note=assump.get("note"),
            )
        elif akey == "our_max" and assump.get("value") is not None:
            extremes_map["our_max"] = to_si_quantity(
                float(assump["value"]),
                str(assump["unit"]),
                "our",
                provenance=assump.get("provenance", "user_assumption"),
                value_nature=assump.get("value_nature", "assumed"),
            )

    constraints_map: dict[str, Quantity] = {}
    for c_item in scen.constraints or []:
        ckey = str(c_item.get("key") or "")
        if ckey and c_item.get("value") is not None:
            constraints_map[ckey] = to_si_quantity(
                float(c_item["value"]),
                str(c_item["unit"]),
                ckey,
                provenance=c_item.get("provenance", "user_assumption"),
                value_nature=c_item.get("value_nature", "assumed"),
            )

    req_ctrls = ["feed_pump"] if proj.process_type == "fed_batch" else []
    proc_summary = ProcessSummary(
        batch_ids=[b.id for b in batches],
        operating=operating_map,
        extremes=extremes_map,
        calibration_status=cal_map,
        high_severity_dq_variables=sorted(high_dq_vars),
        required_instruments=["ph_probe", "do_probe", "temperature_probe"],
        required_controls=req_ctrls,
    )

    med_props = MediumProperties(
        name=med_ctx.get("name"),
        density=med_quantities["density"],
        viscosity=med_quantities["viscosity"],
        oxygen_saturation_concentration=med_quantities["oxygen_saturation_concentration"],
    )

    target_wv_q = to_si_quantity(
        scen.target_working_volume_original,
        scen.target_working_volume_unit,
        "working_volume",
        provenance="manual_entry",
        value_nature="assumed",
    )

    thresh_cfg = ThresholdConfig(**(scen.thresholds or {}))
    scen_cfg = ScenarioConfig(
        criteria=[CriterionSelection(**c) for c in scen.criteria],
        aeration_basis=scen.aeration_basis,  # type: ignore[arg-type]
        target_working_volume=target_wv_q,
        source_kla_point_id=(scen.kla_selection or {}).get("source_point_id"),
        target_kla_point_id=(scen.kla_selection or {}).get("target_point_id"),
        constraints=constraints_map,
        thresholds=thresh_cfg,
    )

    assess_input = AssessmentInput(
        source_vessel=src_spec,
        target_vessel=tgt_spec,
        process=proc_summary,
        medium=med_props,
        scenario=scen_cfg,
        is_synthetic=is_syn,
    )

    output = run_assessment(assess_input)

    # Persist immutable Assessment + children
    assess_row = Assessment(
        organization_id=ctx.organization.id,
        scenario_id=scen.id,
        status="completed",
        engine_version=output.engine_version,
        contract_version=output.contract_version,
        formula_registry_version=output.formula_registry_version,
        rule_registry_version=output.rule_registry_version,
        threshold_config_version=output.threshold_config_version,
        pint_version=output.pint_version,
        inputs_snapshot=assess_input.model_dump(),
        summary=output.summary.model_dump(),
        trade_offs=[t.model_dump() for t in output.trade_offs],
        is_synthetic=output.is_synthetic,
        created_by=ctx.user.id,
    )
    scen.locked_at = datetime.now(timezone.utc)
    db.add(assess_row)
    db.flush()

    for idx, c in enumerate(output.calculations):
        db.add(
            CalculationResultRow(
                organization_id=ctx.organization.id,
                assessment_id=assess_row.id,
                formula_id=c.formula_id,
                formula_name=c.formula_name,
                formula_version=c.formula_version,
                review_status=c.review_status,
                scale=c.scale,
                criterion_id=c.criterion_id,
                equation=c.equation,
                inputs={k: v.model_dump() for k, v in c.inputs.items()},
                output=c.output.model_dump() if c.output else None,
                status=c.status,
                missing_inputs=c.missing_inputs,
                evidence_level=c.evidence_level,
                assumptions=c.assumptions,
                warnings=c.warnings,
                sort_order=idx,
            )
        )

    rule_to_flag_id: dict[str, str] = {}
    for rf in output.risk_flags:
        rf_row = RiskFlagRow(
            organization_id=ctx.organization.id,
            assessment_id=assess_row.id,
            rule_id=rf.rule_id,
            rule_version=rf.rule_version,
            category=rf.category,
            severity=rf.severity,
            outcome=rf.outcome,
            title=rf.title,
            explanation=rf.explanation,
            input_refs=[r.model_dump() for r in rf.input_refs],
            evidence_gap=rf.evidence_gap,
            threshold_used=rf.threshold_used,
            validation_task_codes=rf.validation_task_codes,
        )
        db.add(rf_row)
        db.flush()
        rule_to_flag_id[rf.rule_id] = rf_row.id

    check_to_id: dict[str, str] = {}
    for chk in output.compatibility_checks:
        chk_row = CompatibilityCheckRow(
            organization_id=ctx.organization.id,
            assessment_id=assess_row.id,
            check_id=chk.check_id,
            criterion_id=chk.criterion_id,
            parameter_key=chk.parameter_key,
            title=chk.title,
            required_value_si=chk.required_value_si,
            capability_min_si=chk.capability_min_si,
            capability_max_si=chk.capability_max_si,
            unit_si=chk.unit_si,
            display_unit=chk.display_unit,
            required_display=chk.required_display,
            capability_min_display=chk.capability_min_display,
            capability_max_display=chk.capability_max_display,
            outcome=chk.outcome,
            explanation=chk.explanation,
            input_refs=[r.model_dump() for r in chk.input_refs],
        )
        db.add(chk_row)
        db.flush()
        check_to_id[chk.check_id] = chk_row.id

    for vt in output.validation_tasks:
        db.add(
            ValidationTaskRow(
                organization_id=ctx.organization.id,
                assessment_id=assess_row.id,
                task_code=vt.task_code,
                task_type=vt.task_type,
                title=vt.title,
                description=vt.description,
                priority=vt.priority,
                linked_risk_flag_ids=[
                    rule_to_flag_id[rid]
                    for rid in vt.triggered_by_rule_ids
                    if rid in rule_to_flag_id
                ],
                linked_check_ids=[
                    check_to_id[cid]
                    for cid in vt.triggered_by_check_ids
                    if cid in check_to_id
                ],
                status="open",
            )
        )

    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "assessment.created",
        "assessment",
        assess_row.id,
        {"scenario_id": scen.id, "engine_version": assess_row.engine_version},
    )
    db.commit()
    return _serialize_assessment(assess_row, db)


def _serialize_assessment(a: Assessment, db: Session) -> dict[str, Any]:
    calcs = (
        db.query(CalculationResultRow)
        .filter(CalculationResultRow.assessment_id == a.id)
        .order_by(CalculationResultRow.sort_order.asc())
        .all()
    )
    flags = (
        db.query(RiskFlagRow)
        .filter(RiskFlagRow.assessment_id == a.id)
        .all()
    )
    checks = (
        db.query(CompatibilityCheckRow)
        .filter(CompatibilityCheckRow.assessment_id == a.id)
        .all()
    )
    tasks = (
        db.query(ValidationTaskRow)
        .filter(ValidationTaskRow.assessment_id == a.id)
        .all()
    )
    reviews = (
        db.query(ReviewSignoff)
        .filter(ReviewSignoff.assessment_id == a.id)
        .order_by(ReviewSignoff.created_at.desc())
        .all()
    )
    reports = (
        db.query(ReportRow)
        .filter(ReportRow.assessment_id == a.id)
        .order_by(ReportRow.version.desc())
        .all()
    )

    return {
        "id": a.id,
        "scenario_id": a.scenario_id,
        "status": a.status,
        "engine_version": a.engine_version,
        "contract_version": a.contract_version,
        "formula_registry_version": a.formula_registry_version,
        "rule_registry_version": a.rule_registry_version,
        "threshold_config_version": a.threshold_config_version,
        "pint_version": a.pint_version,
        "is_synthetic": a.is_synthetic,
        "inputs_snapshot": a.inputs_snapshot,
        "summary": a.summary,
        "trade_offs": a.trade_offs,
        "calculations": [
            {
                "id": c.id,
                "formula_id": c.formula_id,
                "formula_name": c.formula_name,
                "formula_version": c.formula_version,
                "review_status": c.review_status,
                "scale": c.scale,
                "criterion_id": c.criterion_id,
                "equation": c.equation,
                "inputs": c.inputs,
                "output": c.output,
                "status": c.status,
                "missing_inputs": c.missing_inputs,
                "evidence_level": c.evidence_level,
                "assumptions": c.assumptions,
                "warnings": c.warnings,
            }
            for c in calcs
        ],
        "compatibility_checks": [
            {
                "id": chk.id,
                "check_id": chk.check_id,
                "criterion_id": chk.criterion_id,
                "parameter_key": chk.parameter_key,
                "title": chk.title,
                "required_value_si": chk.required_value_si,
                "capability_min_si": chk.capability_min_si,
                "capability_max_si": chk.capability_max_si,
                "unit_si": chk.unit_si,
                "display_unit": chk.display_unit,
                "required_display": chk.required_display,
                "capability_min_display": chk.capability_min_display,
                "capability_max_display": chk.capability_max_display,
                "outcome": chk.outcome,
                "explanation": chk.explanation,
                "input_refs": chk.input_refs,
            }
            for chk in checks
        ],
        "risk_flags": [
            {
                "id": f.id,
                "rule_id": f.rule_id,
                "rule_version": f.rule_version,
                "category": f.category,
                "severity": f.severity,
                "outcome": f.outcome,
                "title": f.title,
                "explanation": f.explanation,
                "input_refs": f.input_refs,
                "evidence_gap": f.evidence_gap,
                "threshold_used": f.threshold_used,
                "validation_task_codes": f.validation_task_codes,
            }
            for f in flags
        ],
        "validation_tasks": [
            {
                "id": vt.id,
                "task_code": vt.task_code,
                "task_type": vt.task_type,
                "title": vt.title,
                "description": vt.description,
                "priority": vt.priority,
                "linked_risk_flag_ids": vt.linked_risk_flag_ids,
                "linked_check_ids": vt.linked_check_ids,
                "status": vt.status,
                "waived_reason": vt.waived_reason,
                "updated_at": vt.updated_at.isoformat(),
            }
            for vt in tasks
        ],
        "reviews": [
            {
                "id": rev.id,
                "reviewer_user_id": rev.reviewer_user_id,
                "reviewer_name": rev.reviewer_name,
                "decision": rev.decision,
                "comment": rev.comment,
                "created_at": rev.created_at.isoformat(),
            }
            for rev in reviews
        ],
        "reports": [
            {
                "id": rep.id,
                "version": rep.version,
                "status": rep.status,
                "sha256": rep.sha256,
                "size_bytes": rep.size_bytes,
                "is_synthetic": rep.is_synthetic,
                "generated_at": rep.generated_at.isoformat(),
            }
            for rep in reports
        ],
        "created_at": a.created_at.isoformat(),
    }


@router.get("/scenarios/{scenario_id}/assessments")
def list_scenario_assessments(
    scenario_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    scen = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.organization_id == ctx.organization.id)
        .first()
    )
    if not scen:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Scenario not found")
    rows = (
        db.query(Assessment)
        .filter(Assessment.scenario_id == scen.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )
    return {"items": [_serialize_assessment(a, db) for a in rows]}


@router.get("/assessments/{assessment_id}")
def get_assessment(
    assessment_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    a = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.organization_id == ctx.organization.id,
        )
        .first()
    )
    if not a:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Assessment not found")
    return _serialize_assessment(a, db)


class UpdateValidationTaskRequest(BaseModel):
    status: str  # "open" | "in_progress" | "done" | "waived"
    waived_reason: str | None = None


@router.patch("/validation-tasks/{task_id}")
def update_validation_task(
    task_id: str,
    req: UpdateValidationTaskRequest,
    ctx: AuthContext = Depends(require_roles("scientist", "reviewer", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    vt = (
        db.query(ValidationTaskRow)
        .filter(
            ValidationTaskRow.id == task_id,
            ValidationTaskRow.organization_id == ctx.organization.id,
        )
        .first()
    )
    if not vt:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Validation task not found")
    if req.status not in ("open", "in_progress", "done", "waived"):
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", "Invalid task status"
        )
    if req.status == "waived" and not (req.waived_reason and req.waived_reason.strip()):
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Waiving a validation task requires a non-empty waived_reason",
        )
    vt.status = req.status
    vt.waived_reason = req.waived_reason.strip() if req.waived_reason else None
    vt.updated_by = ctx.user.id
    vt.updated_at = datetime.now(timezone.utc)
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "validation_task.updated",
        "validation_task",
        vt.id,
        {"status": vt.status, "waived_reason": vt.waived_reason},
    )
    db.commit()
    return {
        "id": vt.id,
        "task_code": vt.task_code,
        "status": vt.status,
        "waived_reason": vt.waived_reason,
        "updated_at": vt.updated_at.isoformat(),
    }


class CreateReviewRequest(BaseModel):
    decision: str  # "approved_for_discussion" | "changes_requested"
    comment: str


@router.post("/assessments/{assessment_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_assessment_review(
    assessment_id: str,
    req: CreateReviewRequest,
    ctx: AuthContext = Depends(require_roles("reviewer", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    a = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.organization_id == ctx.organization.id,
        )
        .first()
    )
    if not a:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Assessment not found")
    if req.decision not in ("approved_for_discussion", "changes_requested"):
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Decision must be 'approved_for_discussion' or 'changes_requested'",
        )
    if not req.comment.strip():
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Review comment is required",
        )
    rev = ReviewSignoff(
        organization_id=ctx.organization.id,
        assessment_id=a.id,
        reviewer_user_id=ctx.user.id,
        reviewer_name=ctx.user.full_name,
        decision=req.decision,
        comment=req.comment.strip(),
    )
    db.add(rev)
    db.flush()
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "assessment.reviewed",
        "assessment",
        a.id,
        {"decision": rev.decision},
    )
    db.commit()
    return {
        "id": rev.id,
        "reviewer_user_id": rev.reviewer_user_id,
        "reviewer_name": rev.reviewer_name,
        "decision": rev.decision,
        "comment": rev.comment,
        "created_at": rev.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# 3.7 Reports
# ---------------------------------------------------------------------------
@router.post("/assessments/{assessment_id}/reports", status_code=status.HTTP_201_CREATED)
def generate_assessment_report(
    assessment_id: str,
    ctx: AuthContext = Depends(require_roles("scientist", "reviewer", "org_admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    a = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.organization_id == ctx.organization.id,
        )
        .first()
    )
    if not a:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Assessment not found")

    scen = db.query(Scenario).filter(Scenario.id == a.scenario_id, Scenario.organization_id == ctx.organization.id).first()
    if scen is None:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Scenario not found")
    proj = db.query(Project).filter(Project.id == scen.project_id, Project.organization_id == ctx.organization.id).first()
    if proj is None:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Project not found")
    latest_pv = (
        db.query(PassportVersion)
        .filter(PassportVersion.project_id == proj.id)
        .order_by(PassportVersion.version.desc())
        .first()
    )

    latest_rep = (
        db.query(ReportRow)
        .filter(ReportRow.assessment_id == a.id)
        .order_by(ReportRow.version.desc())
        .first()
    )
    next_ver = (latest_rep.version + 1) if latest_rep else 1

    assess_dict = _serialize_assessment(a, db)
    pdf_bytes = render_transfer_report_pdf(
        project=_serialize_project(proj, db),
        passport=_serialize_passport(latest_pv),
        scenario=_serialize_scenario(scen, db),
        assessment=assess_dict,
        report_version=next_ver,
    )

    storage_key = f"orgs/{ctx.organization.id}/reports/{a.id}/transfer_report_v{next_ver}.pdf"
    sha256 = object_store.put_bytes(storage_key, pdf_bytes, "application/pdf")

    rep = ReportRow(
        organization_id=ctx.organization.id,
        assessment_id=a.id,
        version=next_ver,
        status="generated",
        storage_key=storage_key,
        sha256=sha256,
        size_bytes=len(pdf_bytes),
        template_version="1.0.0",
        is_synthetic=a.is_synthetic,
        generated_by=ctx.user.id,
    )
    db.add(rep)
    db.flush()
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "report.generated",
        "report",
        rep.id,
        {"assessment_id": a.id, "version": next_ver, "sha256": sha256},
    )
    db.commit()
    return {
        "id": rep.id,
        "assessment_id": a.id,
        "version": rep.version,
        "status": rep.status,
        "sha256": rep.sha256,
        "size_bytes": rep.size_bytes,
        "is_synthetic": rep.is_synthetic,
        "generated_at": rep.generated_at.isoformat(),
    }


@router.get("/assessments/{assessment_id}/reports")
def list_assessment_reports(
    assessment_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    a = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.organization_id == ctx.organization.id,
        )
        .first()
    )
    if not a:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Assessment not found")
    reps = (
        db.query(ReportRow)
        .filter(ReportRow.assessment_id == a.id)
        .order_by(ReportRow.version.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": r.id,
                "assessment_id": r.assessment_id,
                "version": r.version,
                "status": r.status,
                "sha256": r.sha256,
                "size_bytes": r.size_bytes,
                "is_synthetic": r.is_synthetic,
                "generated_at": r.generated_at.isoformat(),
            }
            for r in reps
        ]
    }


@router.get("/reports/{report_id}/download")
def download_report(
    report_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    rep = (
        db.query(ReportRow)
        .filter(ReportRow.id == report_id, ReportRow.organization_id == ctx.organization.id)
        .first()
    )
    if not rep:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Report not found")
    pdf_bytes = object_store.get_bytes(rep.storage_key)
    record_audit(
        db,
        ctx.organization.id,
        ctx.user.id,
        "report.downloaded",
        "report",
        rep.id,
        {"version": rep.version},
    )
    db.commit()
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ScaleBridge_Transfer_Report_v{rep.version}.pdf"'
        },
    )


# ---------------------------------------------------------------------------
# 3.6 / 3.8 Science Registries & Audit
# ---------------------------------------------------------------------------
@router.get("/science/formulas")
def get_formula_registry() -> dict[str, Any]:
    return {"items": [f.model_dump() for f in FORMULA_REGISTRY.values()]}


@router.get("/science/criteria")
def get_criteria_registry() -> dict[str, Any]:
    return {"items": [c.model_dump() for c in CRITERIA_REGISTRY.values()]}


@router.get("/science/rules")
def get_rule_registry() -> dict[str, Any]:
    return {"items": [r.model_dump() for r in RULE_REGISTRY.values()]}


@router.get("/science/units")
def get_unit_registry() -> dict[str, Any]:
    return {"variables": VARIABLE_UNIT_SPECS}


@router.get("/audit-events")
def list_audit_events(
    limit: int = Query(default=50, ge=1, le=200),
    ctx: AuthContext = Depends(require_roles("org_admin", "reviewer", "scientist")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.organization_id == ctx.organization.id)
        .order_by(AuditEvent.occurred_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": e.id,
                "actor_user_id": e.actor_user_id,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "occurred_at": e.occurred_at.isoformat(),
                "details": e.details,
            }
            for e in events
        ]
    }
