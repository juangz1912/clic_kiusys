#!/usr/bin/env python3
"""Prueba exhaustiva de todos los endpoints REST."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from urllib import error, request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
TODAY = time.strftime("%Y-%m-%d")
SUFFIX = str(int(time.time()))[-5:]


@dataclass
class Result:
    name: str
    expected: int
    actual: int
    ok: bool


def call(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | str | None]:
    url = f"{BASE_URL.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            code = resp.status
    except error.HTTPError as exc:
        code = exc.code
        raw = exc.read().decode()
    except error.URLError as exc:
        print(f"ERROR de conexion: {exc}")
        sys.exit(1)

    if not raw:
        return code, None
    try:
        return code, json.loads(raw)
    except json.JSONDecodeError:
        return code, raw


def check(name: str, expected: int, actual: int) -> Result:
    status = "OK  " if actual == expected else "FAIL"
    print(f"  {status} {name} (HTTP {actual}, esperado {expected})")
    return Result(name, expected, actual, actual == expected)


def main() -> int:
    results: list[Result] = []
    print("=" * 50)
    print(f"Pruebas en: {BASE_URL}")
    print("=" * 50)

    code, _ = call("GET", "/")
    results.append(check("GET /", 200, code))

    code, body = call("GET", "/api/health")
    results.append(check("GET /api/health", 200, code))
    if isinstance(body, dict):
        assert body.get("status") == "ok"

    code, _ = call("GET", "/docs")
    results.append(check("GET /docs", 200, code))

    vuel_num = f"T{SUFFIX}"
    code, vuelo = call(
        "POST",
        "/api/vuelos",
        {
            "numero_vuelo": vuel_num,
            "origen": "BOG",
            "destino": "MDE",
            "fecha": TODAY,
            "aeronave": "A320",
            "capacidad": 180,
        },
    )
    results.append(check("POST /api/vuelos", 201, code))
    vuelo_id = vuelo["id"] if isinstance(vuelo, dict) else 0

    code, _ = call("GET", "/api/vuelos")
    results.append(check("GET /api/vuelos", 200, code))

    code, _ = call("GET", f"/api/vuelos/{vuelo_id}")
    results.append(check("GET /api/vuelos/{id}", 200, code))

    code, updated = call("PUT", f"/api/vuelos/{vuelo_id}", {"capacidad": 200})
    results.append(check("PUT /api/vuelos/{id}", 200, code))
    if isinstance(updated, dict):
        assert updated["capacidad"] == 200

    code, queried = call("POST", "/api/vuelos/query", {"origen": "BOG", "numero_vuelo": vuel_num})
    results.append(check("POST /api/vuelos/query", 200, code))

    code, _ = call("GET", "/api/vuelos/99999")
    results.append(check("GET /api/vuelos/99999", 404, code))

    doc = f"DOC{SUFFIX}"
    code, pasajero = call(
        "POST",
        "/api/pasajeros",
        {"nombre": "Test User", "documento": doc, "frequent_flyer": "FF999", "tipo": "adulto"},
    )
    results.append(check("POST /api/pasajeros", 201, code))
    pas_id = pasajero["id"] if isinstance(pasajero, dict) else 0

    code, _ = call("GET", "/api/pasajeros")
    results.append(check("GET /api/pasajeros", 200, code))

    code, _ = call("GET", f"/api/pasajeros/{pas_id}")
    results.append(check("GET /api/pasajeros/{id}", 200, code))

    code, _ = call("PUT", f"/api/pasajeros/{pas_id}", {"nombre": "Test Actualizado"})
    results.append(check("PUT /api/pasajeros/{id}", 200, code))

    code, _ = call("POST", "/api/pasajeros/query", {"documento": doc})
    results.append(check("POST /api/pasajeros/query", 200, code))

    code, _ = call("GET", "/api/pasajeros/99999")
    results.append(check("GET /api/pasajeros/99999", 404, code))

    code, asiento = call(
        "POST",
        "/api/asientos-asignados",
        {
            "vuelo_id": vuelo_id,
            "pasajero_id": pas_id,
            "fila": 14,
            "columna": "C",
            "clase": "Y",
            "estado": "seleccionado",
        },
    )
    results.append(check("POST /api/asientos-asignados (hold)", 201, code))
    asi_id = asiento["id"] if isinstance(asiento, dict) else 0
    if isinstance(asiento, dict):
        assert asiento.get("hold_expires_at") is not None

    code, _ = call(
        "POST",
        "/api/asientos-asignados",
        {
            "vuelo_id": vuelo_id,
            "pasajero_id": pas_id,
            "fila": 14,
            "columna": "C",
            "clase": "Y",
            "estado": "seleccionado",
        },
    )
    results.append(check("POST /api/asientos-asignados (conflicto)", 409, code))

    code, _ = call("GET", "/api/asientos-asignados")
    results.append(check("GET /api/asientos-asignados", 200, code))

    code, _ = call("GET", f"/api/asientos-asignados/{asi_id}")
    results.append(check("GET /api/asientos-asignados/{id}", 200, code))

    code, confirmed = call(
        "PUT",
        f"/api/asientos-asignados/{asi_id}",
        {"estado": "asignado", "pasajero_id": pas_id},
    )
    results.append(check("PUT /api/asientos-asignados/{id} (asignar)", 200, code))
    if isinstance(confirmed, dict):
        assert confirmed["estado"] == "asignado"

    code, q_asientos = call(
        "POST",
        "/api/asientos-asignados/query",
        {"vuelo_id": vuelo_id, "estado": "asignado"},
    )
    results.append(check("POST /api/asientos-asignados/query", 200, code))
    if isinstance(q_asientos, list):
        assert len(q_asientos) >= 1

    code, _ = call("GET", "/api/asientos-asignados/99999")
    results.append(check("GET /api/asientos-asignados/99999", 404, code))

    code, _ = call("DELETE", f"/api/asientos-asignados/{asi_id}")
    results.append(check("DELETE /api/asientos-asignados/{id}", 204, code))

    code, _ = call("DELETE", f"/api/pasajeros/{pas_id}")
    results.append(check("DELETE /api/pasajeros/{id}", 204, code))

    code, _ = call("DELETE", f"/api/vuelos/{vuelo_id}")
    results.append(check("DELETE /api/vuelos/{id}", 204, code))

    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed
    print("-" * 50)
    print(f"Resultado: {passed} OK, {failed} FAIL")
    print("=" * 50)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
