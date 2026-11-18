from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.services.chaos_state import ronda_efectiva


class VersionHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-App-Version"] = settings.app_version
        response.headers["X-App-Track"] = settings.app_track
        response.headers["X-Ronda"] = ronda_efectiva()
        return response
