from fastapi import HTTPException

from app.config import settings


def exigir_canary() -> None:
    if settings.app_track != "canary":
        raise HTTPException(status_code=404, detail="api/v3 solo atiende el track canary")
