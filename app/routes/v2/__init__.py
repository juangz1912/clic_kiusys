from fastapi import APIRouter

from app.routes.v2 import flujo, health, metrics

router = APIRouter()
router.include_router(health.router)
router.include_router(flujo.router)
router.include_router(metrics.router)
