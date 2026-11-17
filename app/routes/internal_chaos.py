from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings
from app.services.bitacora import anexar
from app.services.chaos_state import activar_pool, apagar, estado, pausar_telemetria

router = APIRouter()


class ChaosBody(BaseModel):
    tipo: str = Field(pattern="pool|telemetria|off")
    tamano: int = 1
    hold_ms: int = 700
    wait_ms: int = 4000
    ttl_seconds: int = 180
    pausada: bool = True


def _exigir(token: str | None) -> None:
    if not token or token != settings.chaos_token:
        raise HTTPException(status_code=401, detail="token de caos invalido")


@router.get("/internal/chaos")
def ver(x_chaos_token: str | None = Header(default=None)):
    _exigir(x_chaos_token)
    return estado()


@router.get("/internal/latido")
def ver_latido():
    dato = estado()
    return {"latido": dato["latido"], "telemetria": dato["telemetria"]}


@router.get("/internal/senuelo")
def senuelo(request: Request):
    """Señuelo. El flujo normal no llama esta ruta. Tocarla deja alerta."""
    trace = getattr(request.state, "trace_id", "-")
    anexar(f"alerta senuelo tocado trace_id={trace}")
    return {"alerta": "senuelo", "trace_id": trace}


@router.delete("/internal/chaos")
def revertir(x_chaos_token: str | None = Header(default=None)):
    _exigir(x_chaos_token)
    anexar("reversion del pool")
    return apagar()


@router.post("/internal/chaos")
def inyectar(body: ChaosBody, x_chaos_token: str | None = Header(default=None)):
    _exigir(x_chaos_token)
    if body.tipo == "off":
        anexar("apagado manual")
        return apagar()
    if body.tipo == "telemetria":
        anexar(f"telemetria pausada={body.pausada}")
        return pausar_telemetria(body.pausada)
    anexar(f"pool tamano={body.tamano} hold_ms={body.hold_ms} ttl={body.ttl_seconds}")
    return activar_pool(body.tamano, body.hold_ms, body.ttl_seconds, body.wait_ms)
