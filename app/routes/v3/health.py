from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routes.v3.guard import exigir_canary
from app.services.holds import expire_holds

router = APIRouter()


@router.get("/health")
def health_v3(request: Request, db: Session = Depends(get_db)):
    exigir_canary()
    expire_holds(db)
    return {
        "status": "ok",
        "service": "clic-kiusys-pss",
        "api_version": "v3",
        "track": settings.app_track,
        "environment": settings.environment,
        "cloud_provider": settings.cloud_provider,
        "trace_id": getattr(request.state, "trace_id", "unknown"),
    }
