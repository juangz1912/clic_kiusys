from datetime import date

from tests.conftest import client  # noqa: F401


def _create_vuelo(client):
    return client.post(
        "/api/vuelos",
        json={
            "numero_vuelo": "AV100",
            "origen": "BOG",
            "destino": "MDE",
            "fecha": "fecha": "2026-08-199",
            "aeronave": "A320",
            "capacidad": 180,
        },
    )


def _create_pasajero(client, documento="123456"):
    return client.post(
        "/api/pasajeros",
        json={
            "nombre": "Juan Jose Giraldo",
            "documento": documento,
            "frequent_flyer": "FF123",
            "tipo": "adulto",
        },
    )


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_vuelo_crud_and_query(client):
    create = _create_vuelo(client)
    assert create.status_code == 201
    vuelo_id = create.json()["id"]

    get_one = client.get(f"/api/vuelos/{vuelo_id}")
    assert get_one.status_code == 200

    update = client.put(f"/api/vuelos/{vuelo_id}", json={"capacidad": 200})
    assert update.status_code == 200
    assert update.json()["capacidad"] == 200

    query = client.post("/api/vuelos/query", json={"origen": "BOG"})
    assert query.status_code == 200
    assert len(query.json()) == 1

    delete = client.delete(f"/api/vuelos/{vuelo_id}")
    assert delete.status_code == 204


def test_pasajero_crud_and_query(client):
    create = _create_pasajero(client)
    assert create.status_code == 201
    pasajero_id = create.json()["id"]

    query = client.post("/api/pasajeros/query", json={"documento": "123456"})
    assert query.status_code == 200
    assert query.json()[0]["id"] == pasajero_id

    delete = client.delete(f"/api/pasajeros/{pasajero_id}")
    assert delete.status_code == 204


def test_asiento_hold_confirm_and_query(client):
    vuelo_id = _create_vuelo(client).json()["id"]
    pasajero_id = _create_pasajero(client).json()["id"]

    hold = client.post(
        "/api/asientos-asignados",
        json={
            "vuelo_id": vuelo_id,
            "pasajero_id": pasajero_id,
            "fila": 12,
            "columna": "A",
            "clase": "Y",
            "estado": "seleccionado",
        },
    )
    assert hold.status_code == 201
    asiento_id = hold.json()["id"]
    assert hold.json()["hold_expires_at"] is not None

    conflict = client.post(
        "/api/asientos-asignados",
        json={
            "vuelo_id": vuelo_id,
            "pasajero_id": pasajero_id,
            "fila": 12,
            "columna": "A",
            "clase": "Y",
            "estado": "seleccionado",
        },
    )
    assert conflict.status_code == 409

    confirm = client.put(
        f"/api/asientos-asignados/{asiento_id}",
        json={"estado": "asignado", "pasajero_id": pasajero_id},
    )
    assert confirm.status_code == 200
    assert confirm.json()["estado"] == "asignado"
    assert confirm.json()["hold_expires_at"] is None

    query = client.post("/api/asientos-asignados/query", json={"vuelo_id": vuelo_id, "estado": "asignado"})
    assert query.status_code == 200
    assert len(query.json()) == 1


def test_not_found(client):
    assert client.get("/api/vuelos/999").status_code == 404
    assert client.get("/api/pasajeros/999").status_code == 404
    assert client.get("/api/asientos-asignados/999").status_code == 404
