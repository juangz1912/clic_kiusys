from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.entities import AsientoAsignado, EstadoAsiento


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
