from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.clients.api_b import fetch_animal_random
from app.clients.api_c import fetch_imagen_random
from app.database import get_db
from app.models.entities import AsientoAsignado, Pasajero, Vuelo
from app.schemas import AsientoAsignadoRead, PasajeroRead, VueloRead
from app.schemas_v2 import CompanionPayload
from app.services import asiento_service, pasajero_service, vuelo_service

router = APIRouter()


def _one_random(db: Session, model):
    row = db.query(model).order_by(func.random()).first()
    if not row:
        raise HTTPException(status_code=404, detail="No hay registros")
    return row


@router.get("/entidades/vuelos", response_model=list[VueloRead])
def list_vuelos_v2(db: Session = Depends(get_db)):
    return vuelo_service.list_vuelos(db)


@router.get("/entidades/pasajeros", response_model=list[PasajeroRead])
def list_pasajeros_v2(db: Session = Depends(get_db)):
    return pasajero_service.list_pasajeros(db)


@router.get("/entidades/asientos-asignados", response_model=list[AsientoAsignadoRead])
def list_asientos_v2(db: Session = Depends(get_db)):
    return asiento_service.list_asientos(db)


@router.get("/entidades/vuelos/random", response_model=VueloRead)
def random_vuelo(db: Session = Depends(get_db)):
    return _one_random(db, Vuelo)


@router.get("/entidades/pasajeros/random", response_model=PasajeroRead)
def random_pasajero(db: Session = Depends(get_db)):
    return _one_random(db, Pasajero)


@router.get("/entidades/asientos-asignados/random", response_model=AsientoAsignadoRead)
def random_asiento(db: Session = Depends(get_db)):
    return _one_random(db, AsientoAsignado)


@router.get("/entidades/vuelos/{vuelo_id}")
def get_vuelo_con_companeros(vuelo_id: int, request: Request, db: Session = Depends(get_db)):
    """Get by id de Vuelo. Trae un animal random de Angel y una imagen random de Leonardo."""
    vuelo = db.get(Vuelo, vuelo_id)
    if not vuelo:
        raise HTTPException(status_code=404, detail="Vuelo no encontrado")
    trace_id = getattr(request.state, "trace_id", "unknown")
    return {
        "trace_id": trace_id,
        "vuelo": VueloRead.model_validate(vuelo).model_dump(mode="json"),
        "api_b": _companion(fetch_animal_random, trace_id),
        "api_c": _companion(fetch_imagen_random, trace_id),
    }


def _companion(fetch, trace_id: str) -> dict:
    try:
        raw = fetch(trace_id)
    except Exception as exc:
        raw = {"source": "companion", "configured": True, "entity": None, "error": str(exc)}
    return CompanionPayload.model_validate(raw).model_dump(mode="json")
