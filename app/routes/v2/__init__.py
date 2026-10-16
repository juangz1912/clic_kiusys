from fastapi import APIRouter

from app.routes import sli
from app.routes.v2 import demo, entidades, flujo, health, metrics, storage

router = APIRouter()
router.include_router(demo.router)
router.include_router(health.router)
router.include_router(sli.router)
router.include_router(flujo.router)
router.include_router(metrics.router)
router.include_router(entidades.router)
router.include_router(storage.router)
