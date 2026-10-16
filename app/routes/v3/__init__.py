from fastapi import APIRouter

from app.routes.v3 import demo, entidades, health, sli

router = APIRouter()


router.include_router(health.router)
router.include_router(sli.router)
router.include_router(entidades.router)
router.include_router(demo.router)
