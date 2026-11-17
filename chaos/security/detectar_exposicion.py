#!/usr/bin/env python3
"""Detector externo de exposicion (experimento 2). Sale 0 cuando dispara.

Sondea el inventario administrativo a traves del borde cada medio segundo.
Si alguna ruta responde algo distinto de 404, escribe la alerta en JSON con la
marca de tiempo (epoch) y termina. Si la ventana se acaba sin verla, sale 1.

Uso: detectar_exposicion.py URL_BORDE VENTANA_S
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REGLA = Path(__file__).resolve().parent / "detecciones" / "ruta-admin-expuesta.json"
BORDE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8088"
VENTANA = float(sys.argv[2]) if len(sys.argv) > 2 else 20
regla = json.loads(REGLA.read_text())
INVENTARIO = regla["inventario_admin"]
SONDEO = float(regla["sondeo_segundos"])


def estado(ruta: str) -> int:
    req = urllib.request.Request(BORDE + ruta, headers={"X-Trace-Id": "ge2-sonda", "User-Agent": "sonda-exposicion"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0  # borde caido: no es exposicion, es otra alerta


inicio = time.time()
sondeos = 0
while time.time() - inicio < VENTANA:
    sondeos += 1
    vistas = {ruta: estado(ruta) for ruta in INVENTARIO}
    expuestas = {r: c for r, c in vistas.items() if c not in (404, 0)}
    if expuestas:
        print(json.dumps({"alerta": "ruta de administracion expuesta", "rutas": expuestas, "t_alerta": time.time(), "sondeos": sondeos}))
        sys.stdout.flush()
        raise SystemExit(0)
    time.sleep(SONDEO)
print(json.dumps({"alerta": None, "texto": "no disparo", "sondeos": sondeos, "segundos": round(time.time() - inicio, 2)}))
raise SystemExit(1)
