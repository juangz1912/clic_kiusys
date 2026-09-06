from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
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
