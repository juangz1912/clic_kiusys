def test_health_v2(client):
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_version"] == "v2"
    assert "trace_id" in body
    assert response.headers.get("X-Trace-Id")


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

    response = client.post("/api/v2/flujo", json={"vuelo_id": vuelo["id"]})
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v2"
    assert body["local"]["entity"] == "vuelo"
    assert body["local"]["data"]["id"] == vuelo["id"]
    assert len(body["companions"]) == 2


def test_v2_metrics_endpoint(client):
    client.get("/api/v2/health")
    metrics = client.get("/api/v2/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["api_version"] == "v2"
