from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import VueloCreate, VueloQuery, VueloRead, VueloUpdate
from app.services import vuelo_service

router = APIRouter()


@router.post("/vuelos", response_model=VueloRead, status_code=status.HTTP_201_CREATED)
def create_vuelo(payload: VueloCreate, db: Session = Depends(get_db)):
    return vuelo_service.create_vuelo(db, payload)


@router.get("/vuelos", response_model=list[VueloRead])
def list_vuelos(db: Session = Depends(get_db)):
    return vuelo_service.list_vuelos(db)


@router.get("/vuelos/{vuelo_id}", response_model=VueloRead)
def get_vuelo(vuelo_id: int, db: Session = Depends(get_db)):
    return vuelo_service.get_vuelo(db, vuelo_id)


@router.put("/vuelos/{vuelo_id}", response_model=VueloRead)
def update_vuelo(vuelo_id: int, payload: VueloUpdate, db: Session = Depends(get_db)):
    return vuelo_service.update_vuelo(db, vuelo_id, payload)


@router.delete("/vuelos/{vuelo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vuelo(vuelo_id: int, db: Session = Depends(get_db)):
    vuelo_service.delete_vuelo(db, vuelo_id)


@router.post("/vuelos/query", response_model=list[VueloRead])
def query_vuelos_endpoint(payload: VueloQuery, db: Session = Depends(get_db)):
    return vuelo_service.query_vuelos(db, payload.model_dump(exclude_none=True))
