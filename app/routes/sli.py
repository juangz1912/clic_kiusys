from fastapi import APIRouter

from app.config import settings
from app.services.sli import snapshot

router = APIRouter()


@router.get("/sli")
def sli_v2():
    return snapshot(settings.app_version, settings.app_track)
