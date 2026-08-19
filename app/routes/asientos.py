from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import with_fresh_holds
from app.schemas import AsientoAsignadoCreate, AsientoAsignadoQuery, AsientoAsignadoRead, AsientoAsignadoUpdate
from app.services import asiento_service

router = APIRouter()


@router.post("/asientos-asignados", response_model=AsientoAsignadoRead, status_code=status.HTTP_201_CREATED)
def create_asiento(payload: AsientoAsignadoCreate, db: Session = Depends(get_db)):
    return asiento_service.create_asiento(db, payload)


@router.get("/asientos-asignados", response_model=list[AsientoAsignadoRead])
def list_asientos(db: Session = Depends(with_fresh_holds)):
    return asiento_service.list_asientos(db)


@router.get("/asientos-asignados/{asiento_id}", response_model=AsientoAsignadoRead)
def get_asiento(asiento_id: int, db: Session = Depends(with_fresh_holds)):
    return asiento_service.get_asiento(db, asiento_id)


@router.put("/asientos-asignados/{asiento_id}", response_model=AsientoAsignadoRead)
def update_asiento(asiento_id: int, payload: AsientoAsignadoUpdate, db: Session = Depends(with_fresh_holds)):
    return asiento_service.update_asiento(db, asiento_id, payload)


@router.delete("/asientos-asignados/{asiento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asiento(asiento_id: int, db: Session = Depends(get_db)):
    asiento_service.delete_asiento(db, asiento_id)


@router.post("/asientos-asignados/query", response_model=list[AsientoAsignadoRead])
def query_asientos_endpoint(payload: AsientoAsignadoQuery, db: Session = Depends(get_db)):
    return asiento_service.query_asientos(db, payload.model_dump(exclude_none=True))
