from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.v3.guard import exigir_canary
from app.schemas_v3 import EstadoOperativoUpdate, VueloV3Read
from app.services.sli import sumar_estado
from app.services.vuelo_service import get_vuelo, list_vuelos

router = APIRouter()


@router.get("/entidades/vuelos", response_model=list[VueloV3Read])
def listar_vuelos_v3(db: Session = Depends(get_db)):
    exigir_canary()
    return list_vuelos(db)


@router.put("/entidades/vuelos/{vuelo_id}/estado", response_model=VueloV3Read)
def cambiar_estado(vuelo_id: int, payload: EstadoOperativoUpdate, db: Session = Depends(get_db)):
    exigir_canary()
    vuelo = get_vuelo(db, vuelo_id)
    vuelo.estado_operativo = payload.estado_operativo
    db.commit()
    db.refresh(vuelo)
    sumar_estado()
    return vuelo
