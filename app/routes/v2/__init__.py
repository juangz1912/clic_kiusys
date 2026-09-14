from fastapi import APIRouter

from app.routes.v2 import entidades, flujo, health, metrics, storage

router = APIRouter()
router.include_router(health.router)
router.include_router(flujo.router)
router.include_router(metrics.router)
router.include_router(entidades.router)
router.include_router(storage.router)
