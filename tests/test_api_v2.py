from unittest.mock import patch


def test_health_v2(client):
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_version"] == "v2"
    assert "trace_id" in body
    assert response.headers.get("X-Trace-Id")


def _remote(source: str, entity: dict):
    return {"source": source, "configured": True, "entity": entity, "url": f"https://x/{source}"}


def test_flujo_v2_with_local_vuelo(client):
    vuelo = client.post(
        "/api/vuelos",
        json={
            "numero_vuelo": "V2TST",
            "origen": "BOG",
            "destino": "MDE",
            "fecha": "2026-09-14",
            "aeronave": "A320",
            "capacidad": 180,
        },
    ).json()
    pasajero = client.post(
        "/api/pasajeros",
        json={
            "nombre": "Ana Demo",
            "documento": "CC9001",
            "frequent_flyer": "FF1",
            "tipo": "adulto",
        },
    ).json()
    asiento = client.post(
        "/api/asientos-asignados",
        json={
            "vuelo_id": vuelo["id"],
            "pasajero_id": pasajero["id"],
            "fila": 12,
            "columna": "A",
            "clase": "Y",
            "estado": "seleccionado",
        },
    )
    assert asiento.status_code == 201

    b_payload = {
        "animal": _remote("api_b_animal", {"id": 2, "nombre": "Sofi"}),
        "adoptante": _remote("api_b_adoptante", {"id": 1, "nombre": "Luis"}),
        "adopcion": _remote("api_b_adopcion", {"id": 1, "estado": "ACTIVA"}),
    }
    c_payload = {
        "imagen": _remote("api_c_imagen", {"id": 1, "nombre": "imagen1"}),
        "nota_medica": _remote("api_c_nota", {"id": 1, "paciente": "Paciente1"}),
        "documento_generado": _remote("api_c_documento", {"id": 1, "nombre": "Doc1"}),
    }

    with (
        patch("app.services.v2_flow_service.fetch_all_b", return_value=b_payload),
        patch("app.services.v2_flow_service.fetch_all_c", return_value=c_payload),
    ):
        response = client.post("/api/v2/flujo", json={"vuelo_id": vuelo["id"]})

    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v2"
    assert body["local"]["entity"] == "vuelo"
    assert body["local"]["data"]["id"] == vuelo["id"]
    assert len(body["companions"]) == 6
    roles = [v["rol"] for v in body["vinculos"]]
    assert roles == [
        "vuelo-animal-imagen",
        "pasajero-adoptante-nota",
        "asiento-adopcion-documento",
    ]
    assert body["vinculos"][0]["api_b"]["entity"]["nombre"] == "Sofi"
    assert body["vinculos"][0]["api_c"]["entity"]["nombre"] == "imagen1"
    assert body["vinculos"][1]["local"]["entity"] == "pasajero"
    assert body["vinculos"][2]["local"]["entity"] == "asiento_asignado"


def test_v2_metrics_endpoint(client):
    client.get("/api/v2/health")
    metrics = client.get("/api/v2/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["api_version"] == "v2"
