from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.tenant import Organization
from app.models.batch import DataFile, Batch
from app.services.storage import LocalStorageService
from app.services.ingestion_service import IngestionService
from app.schemas.batch import DataFileRead

router = APIRouter()
storage_svc = LocalStorageService()
ingestion_svc = IngestionService()

@router.post("/csv", response_model=DataFileRead)
async def upload_raw_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(('.csv', '.txt')):
        raise HTTPException(status_code=400, detail="Only CSV or plaintext files are supported")

    content = await file.read()
    content_str = content.decode("utf-8", errors="replace")
    lines = content_str.splitlines()
    row_count = max(0, len(lines) - 1)
    col_count = len(lines[0].split(",")) if lines else 0

    org = db.query(Organization).first()
    saved_path = storage_svc.save_file(file.filename, file.file)

    data_file = DataFile(
        tenant_id=org.id if org else "default",
        filename=file.filename,
        format="csv",
        row_count=row_count,
        column_count=col_count,
        storage_path=saved_path
    )
    db.add(data_file)
    db.commit()
    db.refresh(data_file)
    return data_file
