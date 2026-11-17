#!/usr/bin/env python3
"""Puerta: la ronda 1 tiene que dejar el p99 bajo el umbral declarado."""

import json
import sys
from pathlib import Path

UMBRAL = 2000
ruta = Path(__file__).resolve().parent / "results" / "ronda-1.json"
if not ruta.exists():
    print("no hay resultados de la ronda 1")
    raise SystemExit(1)
dato = json.loads(ruta.read_text())
p99 = float(dato["con_fallo"]["p99_ms"])
print(json.dumps({"p99_ms": p99, "umbral": UMBRAL, "pasa": p99 < UMBRAL}))
raise SystemExit(0 if p99 < UMBRAL else 1)
