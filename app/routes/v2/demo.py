from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.demo_flags import FALLO_MENSAJE, flag_activo, set_flag

router = APIRouter(prefix="/demo")


class FalloFlujo(BaseModel):
    activo: bool


def _require_demo() -> None:
    if not settings.demo_failure_enabled:
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/fallo")
def demo_fallo(request: Request):
    """Responde 500 a propósito para disparar la alerta de errores en la sustentación."""
    _require_demo()
    trace_id = getattr(request.state, "trace_id", "unknown")
    raise HTTPException(status_code=500, detail=f"Fallo provocado para la demo de alerta (trace_id={trace_id})")


@router.get("/fallo-flujo", response_model=FalloFlujo)
def get_fallo_flujo(db: Session = Depends(get_db)):
    _require_demo()
    return FalloFlujo(activo=flag_activo(db, FALLO_MENSAJE))


@router.put("/fallo-flujo", response_model=FalloFlujo)
def put_fallo_flujo(payload: FalloFlujo, db: Session = Depends(get_db)):
    """Mientras esté activo, POST /api/v2/mensaje (el paso api_a del orquestador) responde 500."""
    _require_demo()
    return FalloFlujo(activo=set_flag(db, FALLO_MENSAJE, payload.activo))
