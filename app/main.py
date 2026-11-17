import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


_handler = logging.StreamHandler()
_handler.setFormatter(_JsonFormatter())
logging.getLogger("clic_kiusys").handlers = [_handler]
logging.getLogger("clic_kiusys").setLevel(logging.INFO)
logging.getLogger("clic_kiusys").propagate = False

from app.config import settings
from app.telemetry import setup_telemetry
from app.database import init_db
from app.middleware.canary_fault import CanaryFaultMiddleware
from app.middleware.chaos_pool import ChaosPoolMiddleware
from app.middleware.metrics_v2 import V2MetricsMiddleware
from app.middleware.sli import SliMiddleware
from app.middleware.trace_id import TraceIdMiddleware
from app.middleware.version_header import VersionHeaderMiddleware
from app.routes import router
from app.routes.internal_chaos import router as router_chaos
from app.routes.tablero import router as router_tablero
from app.routes.v2 import router as router_v2
from app.routes.v3 import router as router_v3


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment != "test":
        init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(ChaosPoolMiddleware)
app.add_middleware(CanaryFaultMiddleware)
app.add_middleware(SliMiddleware)
app.add_middleware(V2MetricsMiddleware)
app.add_middleware(VersionHeaderMiddleware)
app.add_middleware(TraceIdMiddleware)
# Va después de los middlewares para que el span de OTel los envuelva y el log de
# cada petición salga con el trace_id de la traza.
setup_telemetry(app)
app.include_router(router, prefix="/api")
app.include_router(router_v2, prefix="/api/v2")
app.include_router(router_v3, prefix="/api/v3")
app.include_router(router_tablero)
app.include_router(router_chaos)


@app.get("/")
def root():
    return {
        "message": "Clic KiuSys PSS API",
        "environment": settings.environment,
        "docs": "/docs",
        "api_v2": "/api/v2/health",
    }
