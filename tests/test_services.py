from app.models.entities import EstadoAsiento
from app.services import prepare_asiento_create


def test_prepare_asiento_create_hold():
    data = prepare_asiento_create({"estado": EstadoAsiento.SELECCIONADO})
    assert data["hold_expires_at"] is not None


def test_prepare_asiento_create_asignado():
    data = prepare_asiento_create({"estado": EstadoAsiento.ASIGNADO})
    assert data["hold_expires_at"] is None
