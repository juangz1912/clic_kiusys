import asyncio
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.services.chaos_state import (
    adquirir,
    admision_activa,
    entrar_admision,
    latido,
    salir_admision,
    soltar,
    sumar_rechazo_admision,
)

_LATIDO = Path("chaos/runtime/latido.txt")


class ChaosPoolMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        latido(_LATIDO)
        path = request.url.path
        if not path.endswith("/entidades/vuelos/random"):
            return await call_next(request)

        en_admision = False
        if admision_activa():
            if not entrar_admision(settings.admission_max_inflight):
                sumar_rechazo_admision()
                return JSONResponse(
                    status_code=429,
                    content={"detail": "sin cupo"},
                    headers={"Retry-After": "1"},
                )
            en_admision = True

        resultado = "libre"
        try:
            resultado = await asyncio.to_thread(adquirir)
            if resultado == "agotada":
                return JSONResponse(status_code=503, content={"detail": "pool agotado"})
            return await call_next(request)
        finally:
            soltar(resultado)
            if en_admision:
                salir_admision()
