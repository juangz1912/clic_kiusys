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

    code, flujo, _ = call("POST", "/api/v2/flujo", {}, {"X-Trace-Id": trace or "cli-trace"})
    print("POST /api/v2/flujo ->", code, flujo)
    return 0 if code in (200, 404) else 1


if __name__ == "__main__":
    raise SystemExit(main())
