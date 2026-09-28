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

    client.post(
        "/api/pasajeros",
        json={"nombre": "Ana", "documento": "CCEV2", "tipo": "adulto"},
    )
    pasajeros = client.get("/api/v2/entidades/pasajeros")
    assert pasajeros.status_code == 200
    assert len(pasajeros.json()) >= 1

    asientos = client.get("/api/v2/entidades/asientos-asignados")
    assert asientos.status_code == 200


def test_random_y_get_by_id(client):
    vuelo = client.post(
        "/api/vuelos",
        json={
            "numero_vuelo": "RND1",
            "origen": "BOG",
            "destino": "MDE",
            "fecha": "2026-09-28",
            "aeronave": "A320",
            "capacidad": 100,
        },
    ).json()
    client.post(
        "/api/pasajeros",
        json={"nombre": "Random", "documento": "CCRND", "tipo": "adulto"},
    )
    assert client.get("/api/v2/entidades/vuelos/random").status_code == 200
    assert client.get("/api/v2/entidades/pasajeros/random").status_code == 200

    b = {"source": "api_b_animal_random", "configured": True, "entity": {"id": 2, "nombre": "Sofi"}}
    c = {"source": "api_c_imagen_random", "configured": True, "entity": {"id": 1, "nombre": "imagen1"}}
    from unittest.mock import patch

    with (
        patch("app.routes.v2.entidades.fetch_animal_random", return_value=b),
        patch("app.routes.v2.entidades.fetch_imagen_random", return_value=c),
    ):
        response = client.get(f"/api/v2/entidades/vuelos/{vuelo['id']}", headers={"X-Trace-Id": "comp-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["vuelo"]["id"] == vuelo["id"]
    assert body["api_b"]["entity"]["nombre"] == "Sofi"
    assert body["api_c"]["entity"]["nombre"] == "imagen1"
    assert body["trace_id"] == "comp-1"
