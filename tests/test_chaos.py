from app.services.bitacora import truncar
from app.services.chaos_state import activar_pool, apagar, estado


def test_el_pool_arranca_apagado():
    apagar()
    assert estado()["activo"] is False


def test_el_pool_tiene_ttl_y_se_apaga():
    activar_pool(1, 0, 30, 100)
    assert estado()["activo"] is True
    assert estado()["pool_size"] == 1
    apagar()
    assert estado()["activo"] is False


def test_la_bitacora_no_se_trunca():
    try:
        truncar()
    except PermissionError:
        return
    raise AssertionError("dejo truncar")


def test_sin_cupo_responde_429(client, monkeypatch):
    from app.config import settings
    from app.services import chaos_state

    monkeypatch.setattr(settings, "admission_enabled", True)
    monkeypatch.setattr(settings, "admission_max_inflight", 1)
    chaos_state._inflight = 1
    try:
        respuesta = client.get("/api/v2/entidades/vuelos/random")
        assert respuesta.status_code == 429
        assert respuesta.headers["retry-after"] == "1"
    finally:
        chaos_state._inflight = 0
        apagar()
