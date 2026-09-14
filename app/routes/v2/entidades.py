from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import VueloRead
from app.services import vuelo_service

router = APIRouter()


@router.get("/entidades/vuelos", response_model=list[VueloRead])
def list_vuelos_v2(db: Session = Depends(get_db)):
    """Lista para consumo cross-cloud (Integrantes B/C) bajo contrato api/v2."""
    return vuelo_service.list_vuelos(db)
