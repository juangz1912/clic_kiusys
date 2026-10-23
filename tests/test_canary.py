from canary.estadistica import decidir, prueba_z


def test_cabecera_de_stable(client):
    response = client.get("/api/v2/health")
    assert response.headers["X-App-Version"] == "v2"
    assert response.headers["X-App-Track"] == "stable"


def test_v3_no_atiende_en_stable(client):
    response = client.get("/api/v3/health")
    assert response.status_code == 404


def test_v3_estado_operativo(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "app_track", "canary")
    monkeypatch.setattr(settings, "app_version", "v3")
    creado = client.post(
        "/api/vuelos",
        json={
            "numero_vuelo": "AV900",
            "origen": "BOG",
            "destino": "CTG",
            "fecha": "2026-10-30",
            "aeronave": "A320",
            "capacidad": 180,
        },
    )
    assert creado.status_code == 201
    vuelo_id = creado.json()["id"]
    assert "estado_operativo" not in creado.json()

    lista = client.get("/api/v3/entidades/vuelos")
    assert lista.status_code == 200
    assert lista.json()[0]["estado_operativo"] == "programado"

    cambio = client.put(
        f"/api/v3/entidades/vuelos/{vuelo_id}/estado",
        json={"estado_operativo": "demorado"},
    )
    assert cambio.status_code == 200
    assert cambio.json()["estado_operativo"] == "demorado"
    assert cambio.headers["X-App-Track"] == "canary"

    v2 = client.get("/api/v2/entidades/vuelos")
    assert "estado_operativo" not in v2.json()[0]


def test_falla_inyectada_solo_en_canary(client, monkeypatch):
    from app.config import settings
    from app.services import canary_fault

    monkeypatch.setattr(settings, "app_track", "canary")
    puesto = client.put("/api/v3/demo/degradacion", json={"modo": "errores", "porcentaje": 100})
    assert puesto.status_code == 200
    try:
        fallido = client.get("/api/v2/entidades/vuelos")
        assert fallido.status_code == 500
        assert fallido.headers["X-App-Track"] == "canary"
        assert client.get("/api/v2/health").status_code == 200
        apagado = client.put("/api/v3/demo/degradacion", json={"modo": "off", "porcentaje": 0})
        assert apagado.status_code == 200
    finally:
        canary_fault.configurar("off", 0)
    monkeypatch.setattr(settings, "app_track", "stable")
    sano = client.get("/api/v2/entidades/vuelos")
    assert sano.status_code == 200


def test_z_aborta_si_el_canary_falla_mas():
    z = prueba_z(0, 50, 20, 50)
    assert z is not None and z > 1.96
    decision = decidir(
        {"requests": 50, "errors_5xx": 0, "error_ratio_5xx": 0, "latency_p95_ms": 20},
        {"requests": 50, "errors_5xx": 20, "error_ratio_5xx": 0.4, "latency_p95_ms": 20},
        minimo=50,
        z_max=1.96,
        ratio_5xx_max=0.05,
        p95_factor=2,
        p95_piso_ms=400,
    )
    assert decision == "abortar"


def test_z_pausa_sin_muestra():
    decision = decidir(
        {"requests": 3, "errors_5xx": 0, "error_ratio_5xx": 0, "latency_p95_ms": 10},
        {"requests": 3, "errors_5xx": 0, "error_ratio_5xx": 0, "latency_p95_ms": 10},
        minimo=50,
        z_max=1.96,
        ratio_5xx_max=0.05,
        p95_factor=2,
        p95_piso_ms=400,
    )
    assert decision == "pausar"
