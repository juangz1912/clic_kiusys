#!/usr/bin/env python3
"""Smoke test para endpoints api/v2."""

import json
import sys
from urllib import request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"


def call(method: str, path: str, body: dict | None = None, headers: dict | None = None):
    url = f"{BASE.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = request.Request(url, data=data, headers=hdrs, method=method)
    with request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else None, resp.headers


def main() -> int:
    print(f"Probando v2 en {BASE}")
    code, health, headers = call("GET", "/api/v2/health")
    assert code == 200, health
    trace = headers.get("X-Trace-Id") or health.get("trace_id")
    print("OK health v2", health)

    code, metrics, _ = call("GET", "/api/v2/metrics")
    assert code == 200
    print("OK metrics v2", metrics)

    code, flujo, _ = call(
        "POST",
        "/api/v2/flujo",
        {"origen": "BOG", "destino": "MDE"},
        {"X-Trace-Id": trace or "cli-trace"},
    )
    print("POST /api/v2/flujo ->", code, flujo)
    if code != 200:
        return 1
    companions = flujo.get("companions") or []
    with_entity = [c for c in companions if c.get("entity")]
    if len(with_entity) >= 6:
        print("OK flujo v2 con entidades B y C via HTTP")
    elif len(with_entity) >= 2:
        print("AVISO: faltan entidades remotas; revisa API_B/C")
    elif len(with_entity) == 1:
        print("AVISO: solo una entidad remota; revisa API_B/C")
    else:
        print("AVISO: sin entidades remotas (stub o sin seed v1)")

    vinculos = flujo.get("vinculos") or []
    if vinculos:
        print("OK vinculos", [v.get("rol") for v in vinculos])

    os_meta = flujo.get("object_storage") or {}
    if os_meta.get("stored"):
        path = os_meta.get("get_url", "")
        if path.startswith("http"):
            path = path.replace(BASE.rstrip("/"), "")
        code2, snap, _ = call("GET", path, None, {"X-Trace-Id": trace or "cli-trace"})
        if code2 == 200 and snap:
            print("OK object storage snapshot", snap.get("trace_id"))
        else:
            print("FALLO object storage GET", code2)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
