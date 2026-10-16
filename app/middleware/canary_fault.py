from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.services.canary_fault import aplicar


def _afecta(path: str) -> bool:
    """El health, el SLI y el interruptor de la falla no se degradan.

    Así el balanceador sigue viendo el backend sano y se puede apagar la inyección.
    """
    if path.endswith("/health") or path.endswith("/sli") or path.endswith("/demo/degradacion"):
        return False
    return True


class CanaryFaultMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if settings.app_track == "canary" and path.startswith("/api") and _afecta(path):
            codigo = aplicar()
            if codigo == 500:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Fallo inyectado en el track canary"},
                )
        return await call_next(request)
