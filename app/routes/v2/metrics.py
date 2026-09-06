from fastapi import APIRouter

from app.middleware.metrics_v2 import get_v2_metrics_snapshot

router = APIRouter()


@router.get("/metrics")
def v2_metrics():
    return {"api_version": "v2", "endpoints": get_v2_metrics_snapshot()}
