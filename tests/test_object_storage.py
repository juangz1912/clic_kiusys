def test_flujo_persists_object_storage(client):
    vuelo = client.post(
        "/api/vuelos",
        json={
            "numero_vuelo": "OS1",
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
    assert body["object_storage"]["stored"] is True
    assert body["object_storage"]["object_key"].startswith("flujo/")

    trace_id = body["trace_id"]
    snapshot = client.get(f"/api/v2/storage/flujo/{trace_id}")
    assert snapshot.status_code == 200
    assert snapshot.json()["trace_id"] == trace_id


def test_entidades_vuelos_v2(client):
    client.post(
        "/api/vuelos",
        json={
            "numero_vuelo": "EV2",
            "origen": "BOG",
            "destino": "CLO",
            "fecha": "2026-09-14",
            "aeronave": "B737",
            "capacidad": 160,
        },
    )
    response = client.get("/api/v2/entidades/vuelos")
    assert response.status_code == 200
    assert len(response.json()) >= 1
