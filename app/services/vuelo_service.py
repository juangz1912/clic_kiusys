from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import Vuelo
from app.schemas import VueloCreate, VueloUpdate


def create_vuelo(db: Session, payload: VueloCreate) -> Vuelo:
    vuelo = Vuelo(**payload.model_dump())
    db.add(vuelo)
    db.commit()
    db.refresh(vuelo)
    return vuelo


def list_vuelos(db: Session) -> list[Vuelo]:
    return db.query(Vuelo).order_by(Vuelo.id).all()


def get_vuelo(db: Session, vuelo_id: int) -> Vuelo:
    vuelo = db.get(Vuelo, vuelo_id)
    if not vuelo:
        raise HTTPException(status_code=404, detail="Vuelo no encontrado")
    return vuelo


def update_vuelo(db: Session, vuelo_id: int, payload: VueloUpdate) -> Vuelo:
    vuelo = get_vuelo(db, vuelo_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(vuelo, key, value)
    db.commit()
    db.refresh(vuelo)
    return vuelo


def delete_vuelo(db: Session, vuelo_id: int) -> None:
    vuelo = get_vuelo(db, vuelo_id)
    db.delete(vuelo)
    db.commit()


def query_vuelos(db: Session, filters: dict) -> list[Vuelo]:
    query = db.query(Vuelo)
    if filters.get("origen"):
        query = query.filter(Vuelo.origen == filters["origen"].upper())
    if filters.get("destino"):
        query = query.filter(Vuelo.destino == filters["destino"].upper())
    if filters.get("fecha"):
        query = query.filter(Vuelo.fecha == filters["fecha"])
    if filters.get("numero_vuelo"):
        query = query.filter(Vuelo.numero_vuelo == filters["numero_vuelo"].upper())
    return query.order_by(Vuelo.fecha).all()
