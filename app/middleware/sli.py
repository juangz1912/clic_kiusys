import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.services.sli import registrar


class SliMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not path.startswith("/api") or path.endswith("/health") or path.endswith("/sli"):
            return await call_next(request)
        inicio = time.perf_counter()
        response = await call_next(request)
        registrar(response.status_code, (time.perf_counter() - inicio) * 1000)
        return response
