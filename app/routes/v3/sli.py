from fastapi import APIRouter

from app.config import settings
from app.routes.v3.guard import exigir_canary
from app.services.sli import snapshot

router = APIRouter()


@router.get("/sli")
def sli_v3():
    exigir_canary()
    return snapshot(settings.app_version, settings.app_track)
