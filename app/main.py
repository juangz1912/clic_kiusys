from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import init_db
from app.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment != "test":
        init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Clic KiuSys PSS API",
        "environment": settings.environment,
        "docs": "/docs",
    }
