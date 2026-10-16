from fastapi import APIRouter

from app.routes.v3.guard import exigir_canary
from app.schemas_v3 import Degradacion
from app.services.canary_fault import configurar, estado

router = APIRouter()


@router.get("/demo/degradacion")
def ver_degradacion():
    exigir_canary()
    return estado()


@router.put("/demo/degradacion")
def poner_degradacion(payload: Degradacion):
    exigir_canary()
    return configurar(payload.modo, payload.porcentaje)
