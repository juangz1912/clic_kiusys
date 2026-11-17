import importlib.util
from pathlib import Path

import pytest

from app.config import settings
from app.services import identidad
from app.services.bitacora import RUTA

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("detectar_identidad", ROOT / "chaos/security/detectar_identidad.py")
detectar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(detectar)


@pytest.fixture()
def estricta(monkeypatch):
    monkeypatch.setattr(settings, "identidad_estricta", True)
    monkeypatch.setattr(settings, "identidad_origenes", "testclient")
    identidad.limpiar()
    yield
    identidad.limpiar()


def _nuevas(antes: str) -> str:
    return RUTA.read_text(encoding="utf-8").replace(antes, "") if RUTA.exists() else ""


def _antes() -> str:
    return RUTA.read_text(encoding="utf-8") if RUTA.exists() else ""


def test_sin_modo_estricto_el_token_estatico_sigue_sirviendo(client):
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": settings.chaos_token})
    assert respuesta.status_code == 200


def test_el_coordinador_lee_con_su_alcance_desde_su_origen(client, estricta):
    antes = _antes()
    token = identidad.emitir("coordinador", "chaos:leer")
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": token, "X-Trace-Id": "id-ok"})
    assert respuesta.status_code == 200
    assert "identidad ok sub=coordinador" in _nuevas(antes)


def test_el_token_estatico_se_rechaza(client, estricta):
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": settings.chaos_token})
    assert respuesta.status_code == 401
    assert "token_estatico" in respuesta.json()["detail"]


def test_otro_origen_se_rechaza(client, estricta, monkeypatch):
    monkeypatch.setattr(settings, "identidad_origenes", "127.0.0.1")
    antes = _antes()
    token = identidad.emitir("coordinador", "chaos:leer")
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": token, "X-Trace-Id": "id-origen"})
    assert respuesta.status_code == 403
    assert "motivo=origen" in _nuevas(antes)


def test_alcance_no_previsto_se_rechaza(client, estricta):
    token = identidad.emitir("coordinador", "chaos:telemetria")
    respuesta = client.post("/internal/chaos", json={"tipo": "pool", "ttl_seconds": 1}, headers={"x-chaos-token": token})
    assert respuesta.status_code == 403
    assert "alcance" in respuesta.json()["detail"]


def test_token_vencido_se_rechaza(client, estricta, monkeypatch):
    token = identidad.emitir("coordinador", "chaos:leer", ttl_s=1)
    real = identidad.time.time
    monkeypatch.setattr(identidad.time, "time", lambda: real() + 5)
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": token})
    assert respuesta.status_code == 401
    assert "vencido" in respuesta.json()["detail"]


def test_el_ttl_no_pasa_del_maximo():
    claims = identidad.leer(identidad.emitir("coordinador", "chaos:leer", ttl_s=3600))
    assert claims["exp"] - claims["iat"] == settings.identidad_ttl_s


def test_firma_alterada_se_rechaza(client, estricta):
    token = identidad.emitir("coordinador", "chaos:leer")
    cabecera, cuerpo, firma = token.split(".")
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": f"{cabecera}.{cuerpo}.{firma[::-1]}"})
    assert respuesta.status_code == 401


def test_revocar_corta_la_credencial(client, estricta):
    robada = identidad.emitir("coordinador", "chaos:leer")
    jti = identidad.leer(robada)["jti"]
    revocar = identidad.emitir("defensor", "identidad:revocar")
    assert client.post("/internal/identidad/revocar", json={"jti": jti}, headers={"x-chaos-token": revocar}).status_code == 200
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": robada})
    assert respuesta.status_code == 401
    assert "revocado" in respuesta.json()["detail"]


def test_sin_modo_estricto_no_hay_revocacion(client):
    respuesta = client.post("/internal/identidad/revocar", json={"jti": "x"}, headers={"x-chaos-token": settings.chaos_token})
    assert respuesta.status_code == 404


def test_regla_caso_positivo():
    linea = ("identidad rechazo motivo=origen sub=coordinador jti=abc alcance_pedido=chaos:telemetria "
             "alcance_token=chaos:telemetria origen=127.0.0.2 trace_id=id-r1-origen")
    alertas = detectar.evaluar([linea])
    assert len(alertas) == 1
    assert alertas[0]["motivo"] == "origen"
    assert alertas[0]["trace_id"] == "id-r1-origen"
    assert alertas[0]["severidad"] == "alta"


def test_regla_caso_negativo():
    lineas = [
        "identidad ok sub=coordinador jti=abc alcance=chaos:leer origen=127.0.0.1 trace_id=id-r1-normal-0",
        "telemetria pausada=False",
        "alerta senuelo tocado trace_id=gd-senuelo",
    ]
    assert detectar.evaluar(lineas) == []
