from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import Pasajero
from app.schemas import PasajeroCreate, PasajeroUpdate


def create_pasajero(db: Session, payload: PasajeroCreate) -> Pasajero:
    pasajero = Pasajero(**payload.model_dump())
    db.add(pasajero)
    db.commit()
    db.refresh(pasajero)
    return pasajero


def list_pasajeros(db: Session) -> list[Pasajero]:
    return db.query(Pasajero).order_by(Pasajero.id).all()


def get_pasajero(db: Session, pasajero_id: int) -> Pasajero:
    pasajero = db.get(Pasajero, pasajero_id)
    if not pasajero:
        raise HTTPException(status_code=404, detail="Pasajero no encontrado")
    return pasajero


def update_pasajero(db: Session, pasajero_id: int, payload: PasajeroUpdate) -> Pasajero:
    pasajero = get_pasajero(db, pasajero_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(pasajero, key, value)
    db.commit()
    db.refresh(pasajero)
    return pasajero


def delete_pasajero(db: Session, pasajero_id: int) -> None:
    pasajero = get_pasajero(db, pasajero_id)
    db.delete(pasajero)
    db.commit()


def query_pasajeros(db: Session, filters: dict) -> list[Pasajero]:
    query = db.query(Pasajero)
    if filters.get("documento"):
        query = query.filter(Pasajero.documento == filters["documento"])
    if filters.get("nombre"):
        query = query.filter(Pasajero.nombre.ilike(f"%{filters['nombre']}%"))
    if filters.get("tipo"):
        query = query.filter(Pasajero.tipo == filters["tipo"])
    return query.order_by(Pasajero.nombre).all()
