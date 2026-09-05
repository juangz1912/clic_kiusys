from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas_v2 import HealthV2Response
from app.services.holds import expire_holds

router = APIRouter()


@router.get("/health", response_model=HealthV2Response)
def health_v2(request: Request, db: Session = Depends(get_db)):
    expire_holds(db)
    trace_id = getattr(request.state, "trace_id", "unknown")
    return HealthV2Response(
        status="ok",
        service="clic-kiusys-pss",
        environment=settings.environment,
        cloud_provider=settings.cloud_provider,
        oke_cluster_name=settings.oke_cluster_name,
        trace_id=trace_id,
    )
