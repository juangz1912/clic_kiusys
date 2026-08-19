from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import AsientoAsignado, EstadoAsiento, Pasajero, Vuelo
from app.schemas import AsientoAsignadoCreate, AsientoAsignadoUpdate
from app.services.holds import confirm_asiento, expire_holds, prepare_asiento_create


def create_asiento(db: Session, payload: AsientoAsignadoCreate) -> AsientoAsignado:
    expire_holds(db)
    if not db.get(Vuelo, payload.vuelo_id):
        raise HTTPException(status_code=404, detail="Vuelo no encontrado")
    if payload.pasajero_id and not db.get(Pasajero, payload.pasajero_id):
        raise HTTPException(status_code=404, detail="Pasajero no encontrado")

    exists = (
        db.query(AsientoAsignado)
        .filter(
            AsientoAsignado.vuelo_id == payload.vuelo_id,
            AsientoAsignado.fila == payload.fila,
            AsientoAsignado.columna == payload.columna.upper(),
            AsientoAsignado.estado.in_([EstadoAsiento.SELECCIONADO, EstadoAsiento.ASIGNADO]),
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Asiento no disponible")

    data = prepare_asiento_create(payload.model_dump())
    data["columna"] = data["columna"].upper()
    asiento = AsientoAsignado(**data)
    db.add(asiento)
    db.commit()
    db.refresh(asiento)
    return asiento


def list_asientos(db: Session) -> list[AsientoAsignado]:
    expire_holds(db)
    return db.query(AsientoAsignado).order_by(AsientoAsignado.id).all()


def get_asiento(db: Session, asiento_id: int) -> AsientoAsignado:
    expire_holds(db)
    asiento = db.get(AsientoAsignado, asiento_id)
    if not asiento:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return asiento


def update_asiento(db: Session, asiento_id: int, payload: AsientoAsignadoUpdate) -> AsientoAsignado:
    expire_holds(db)
    asiento = get_asiento(db, asiento_id)

    data = payload.model_dump(exclude_unset=True)
    if data.get("estado") == "asignado":
        if not data.get("pasajero_id") and not asiento.pasajero_id:
            raise HTTPException(status_code=400, detail="Se requiere pasajero_id para asignar")
        pasajero_id = data.get("pasajero_id") or asiento.pasajero_id
        if not db.get(Pasajero, pasajero_id):
            raise HTTPException(status_code=404, detail="Pasajero no encontrado")
        confirm_asiento(asiento, pasajero_id)
        db.commit()
        db.refresh(asiento)
        return asiento

    for key, value in data.items():
        setattr(asiento, key, value)
    db.commit()
    db.refresh(asiento)
    return asiento


def delete_asiento(db: Session, asiento_id: int) -> None:
    asiento = db.get(AsientoAsignado, asiento_id)
    if not asiento:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    db.delete(asiento)
    db.commit()


def query_asientos(db: Session, filters: dict) -> list[AsientoAsignado]:
    expire_holds(db)
    query = db.query(AsientoAsignado)
    if filters.get("vuelo_id"):
        query = query.filter(AsientoAsignado.vuelo_id == filters["vuelo_id"])
    if filters.get("pasajero_id"):
        query = query.filter(AsientoAsignado.pasajero_id == filters["pasajero_id"])
    if filters.get("estado"):
        query = query.filter(AsientoAsignado.estado == filters["estado"])
    if filters.get("clase"):
        query = query.filter(AsientoAsignado.clase == filters["clase"])
    return query.order_by(AsientoAsignado.fila, AsientoAsignado.columna).all()
