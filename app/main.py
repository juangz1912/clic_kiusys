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
from app.middleware.metrics_v2 import V2MetricsMiddleware
from app.middleware.trace_id import TraceIdMiddleware
from app.routes import router
from app.routes.v2 import router as router_v2


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment != "test":
        init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
setup_telemetry(app)
app.add_middleware(V2MetricsMiddleware)
app.add_middleware(TraceIdMiddleware)
app.include_router(router, prefix="/api")
app.include_router(router_v2, prefix="/api/v2")


@app.get("/")
def root():
    return {
        "message": "Clic KiuSys PSS API",
        "environment": settings.environment,
        "docs": "/docs",
        "api_v2": "/api/v2/health",
    }
