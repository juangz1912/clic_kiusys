from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PasajeroCreate, PasajeroQuery, PasajeroRead, PasajeroUpdate
from app.services import pasajero_service

router = APIRouter()


@router.post("/pasajeros", response_model=PasajeroRead, status_code=status.HTTP_201_CREATED)
def create_pasajero(payload: PasajeroCreate, db: Session = Depends(get_db)):
    return pasajero_service.create_pasajero(db, payload)


@router.get("/pasajeros", response_model=list[PasajeroRead])
def list_pasajeros(db: Session = Depends(get_db)):
    return pasajero_service.list_pasajeros(db)


@router.get("/pasajeros/{pasajero_id}", response_model=PasajeroRead)
def get_pasajero(pasajero_id: int, db: Session = Depends(get_db)):
    return pasajero_service.get_pasajero(db, pasajero_id)


@router.put("/pasajeros/{pasajero_id}", response_model=PasajeroRead)
def update_pasajero(pasajero_id: int, payload: PasajeroUpdate, db: Session = Depends(get_db)):
    return pasajero_service.update_pasajero(db, pasajero_id, payload)


@router.delete("/pasajeros/{pasajero_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pasajero(pasajero_id: int, db: Session = Depends(get_db)):
    pasajero_service.delete_pasajero(db, pasajero_id)


@router.post("/pasajeros/query", response_model=list[PasajeroRead])
def query_pasajeros_endpoint(payload: PasajeroQuery, db: Session = Depends(get_db)):
    return pasajero_service.query_pasajeros(db, payload.model_dump(exclude_none=True))
