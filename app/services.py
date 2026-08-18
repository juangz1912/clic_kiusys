from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.entities import AsientoAsignado, EstadoAsiento, Pasajero, Vuelo


def expire_holds(db: Session) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    holds = (
        db.query(AsientoAsignado)
        .filter(
            AsientoAsignado.estado == EstadoAsiento.SELECCIONADO,
            AsientoAsignado.hold_expires_at.isnot(None),
            AsientoAsignado.hold_expires_at < now,
        )
        .all()
    )
    for seat in holds:
        seat.estado = EstadoAsiento.EXPIRADO
        seat.pasajero_id = None
        seat.hold_expires_at = None
    if holds:
        db.commit()


def prepare_asiento_create(data: dict) -> dict:
    payload = dict(data)
    if payload.get("estado") == EstadoAsiento.SELECCIONADO:
        payload["hold_expires_at"] = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            minutes=settings.hold_minutes
        )
    elif payload.get("estado") == EstadoAsiento.ASIGNADO:
        payload["hold_expires_at"] = None
    return payload


def confirm_asiento(asiento: AsientoAsignado, pasajero_id: int) -> None:
    asiento.estado = EstadoAsiento.ASIGNADO
    asiento.pasajero_id = pasajero_id
    asiento.hold_expires_at = None


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


def query_pasajeros(db: Session, filters: dict) -> list[Pasajero]:
    query = db.query(Pasajero)
    if filters.get("documento"):
        query = query.filter(Pasajero.documento == filters["documento"])
    if filters.get("nombre"):
        query = query.filter(Pasajero.nombre.ilike(f"%{filters['nombre']}%"))
    if filters.get("tipo"):
        query = query.filter(Pasajero.tipo == filters["tipo"])
    return query.order_by(Pasajero.nombre).all()


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
