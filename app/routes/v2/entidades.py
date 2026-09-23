from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AsientoAsignadoRead, PasajeroRead, VueloRead
from app.services import asiento_service, pasajero_service, vuelo_service

router = APIRouter()


@router.get("/entidades/vuelos", response_model=list[VueloRead])
def list_vuelos_v2(db: Session = Depends(get_db)):
    """Lista para consumo cross-cloud (Integrantes B/C) bajo contrato api/v2."""
    return vuelo_service.list_vuelos(db)


@router.get("/entidades/pasajeros", response_model=list[PasajeroRead])
def list_pasajeros_v2(db: Session = Depends(get_db)):
    return pasajero_service.list_pasajeros(db)


@router.get("/entidades/asientos-asignados", response_model=list[AsientoAsignadoRead])
def list_asientos_v2(db: Session = Depends(get_db)):
    return asiento_service.list_asientos(db)
