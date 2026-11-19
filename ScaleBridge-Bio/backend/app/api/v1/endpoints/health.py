from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ScaleBridge Bio API",
        "version": "1.0.0"
    }
