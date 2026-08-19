from fastapi import APIRouter

from app.routes import asientos, health, pasajeros, vuelos

router = APIRouter()
router.include_router(health.router)
router.include_router(vuelos.router)
router.include_router(pasajeros.router)
router.include_router(asientos.router)
