from fastapi import APIRouter, HTTPException, Request

from app.config import settings

router = APIRouter(prefix="/demo")


@router.get("/fallo")
def demo_fallo(request: Request):
    """Responde 500 a propósito para disparar la alerta de errores en la sustentación."""
    if not settings.demo_failure_enabled:
        raise HTTPException(status_code=404, detail="Not Found")
    trace_id = getattr(request.state, "trace_id", "unknown")
    raise HTTPException(status_code=500, detail=f"Fallo provocado para la demo de alerta (trace_id={trace_id})")
