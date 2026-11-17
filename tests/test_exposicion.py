"""Experimento 2: el token publico del repo no abre el interruptor en produccion."""

from app.config import settings
from app.services.chaos_state import apagar


def test_token_por_defecto_rechazado_en_produccion(client, monkeypatch):
    monkeypatch.setattr(settings, "environment", "produccion")
    monkeypatch.setattr(settings, "chaos_token", "caos-local")
    respuesta = client.post("/internal/chaos", headers={"x-chaos-token": "caos-local"}, json={"tipo": "pool", "ttl_seconds": 5})
    assert respuesta.status_code == 403
    apagar()


def test_token_propio_si_abre_en_produccion(client, monkeypatch):
    monkeypatch.setattr(settings, "environment", "produccion")
    monkeypatch.setattr(settings, "chaos_token", "token-de-la-ventana")
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": "token-de-la-ventana"})
    assert respuesta.status_code == 200


def test_fuera_de_produccion_el_defecto_sigue_sirviendo(client, monkeypatch):
    monkeypatch.setattr(settings, "environment", "pruebas")
    monkeypatch.setattr(settings, "chaos_token", "caos-local")
    respuesta = client.get("/internal/chaos", headers={"x-chaos-token": "caos-local"})
    assert respuesta.status_code == 200


def test_sin_token_sigue_siendo_401(client, monkeypatch):
    monkeypatch.setattr(settings, "environment", "produccion")
    assert client.get("/internal/chaos").status_code == 401
