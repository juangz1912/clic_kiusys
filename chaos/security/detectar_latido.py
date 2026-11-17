#!/usr/bin/env python3
"""Alerta si el latido de la API no avanza. Sale 0 cuando dispara."""

import json
import sys
import time
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8011"
UMBRAL = float(sys.argv[2]) if len(sys.argv) > 2 else 3
inicio = time.time()
ultimo = None
for _ in range(40):
    try:
        with urllib.request.urlopen(BASE + "/internal/latido", timeout=2) as resp:
            dato = json.load(resp)
    except Exception:
        time.sleep(0.5)
        continue
    marca = dato.get("latido")
    if not dato.get("telemetria"):
        if ultimo is None:
            ultimo = marca
        elif marca == ultimo and time.time() - inicio >= UMBRAL:
            print(json.dumps({"alerta": "ausencia de latido", "mttd_s": round(time.time() - inicio, 2)}))
            raise SystemExit(0)
    else:
        ultimo = marca
        inicio = time.time()
    time.sleep(0.5)
print("no disparo")
raise SystemExit(1)
