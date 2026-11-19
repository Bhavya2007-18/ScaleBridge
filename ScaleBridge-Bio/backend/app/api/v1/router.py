from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    projects,
    batches,
    uploads,
    vessels,
    scenarios,
    assessments,
    reports
)

router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(batches.router, prefix="/batches", tags=["Batches"])
router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
router.include_router(vessels.router, prefix="/vessels", tags=["Vessels"])
router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
router.include_router(assessments.router, prefix="/assessments", tags=["Assessments"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
