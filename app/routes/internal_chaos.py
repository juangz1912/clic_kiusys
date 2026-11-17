from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings
from app.services import identidad
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


class RevocarBody(BaseModel):
    jti: str


_ALCANCE_POR_TIPO = {"off": "chaos:revertir", "telemetria": "chaos:telemetria", "pool": "chaos:pool"}


def _exigir(token: str | None, request: Request, alcance: str) -> None:
    if not settings.identidad_estricta:
        if not token or token != settings.chaos_token:
            raise HTTPException(status_code=401, detail="token de caos invalido")
        return
    origen = request.client.host if request.client else "-"
    trace = getattr(request.state, "trace_id", "-")
    try:
        identidad.validar(token, alcance, origen, trace)
    except identidad.Rechazo as exc:
        raise HTTPException(status_code=exc.status, detail=f"credencial rechazada: {exc.motivo}") from exc


@router.get("/internal/chaos")
def ver(request: Request, x_chaos_token: str | None = Header(default=None)):
    _exigir(x_chaos_token, request, "chaos:leer")
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
def revertir(request: Request, x_chaos_token: str | None = Header(default=None)):
    _exigir(x_chaos_token, request, "chaos:revertir")
    anexar("reversion del pool")
    return apagar()


@router.post("/internal/chaos")
def inyectar(body: ChaosBody, request: Request, x_chaos_token: str | None = Header(default=None)):
    _exigir(x_chaos_token, request, _ALCANCE_POR_TIPO[body.tipo])
    if body.tipo == "off":
        anexar("apagado manual")
        return apagar()
    if body.tipo == "telemetria":
        anexar(f"telemetria pausada={body.pausada}")
        return pausar_telemetria(body.pausada)
    anexar(f"pool tamano={body.tamano} hold_ms={body.hold_ms} ttl={body.ttl_seconds}")
    return activar_pool(body.tamano, body.hold_ms, body.ttl_seconds, body.wait_ms)


@router.post("/internal/identidad/revocar")
def revocar(body: RevocarBody, request: Request, x_chaos_token: str | None = Header(default=None)):
    if not settings.identidad_estricta:
        raise HTTPException(status_code=404, detail="no hay revocacion: la credencial es estatica")
    _exigir(x_chaos_token, request, "identidad:revocar")
    identidad.revocar(body.jti)
    trace = getattr(request.state, "trace_id", "-")
    anexar(f"contencion identidad jti={body.jti} revocado trace_id={trace}")
    return {"revocado": body.jti, "revocados": identidad.revocados()}
