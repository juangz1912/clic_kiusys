#!/usr/bin/env python3
"""Aplica la regla uso-credencial-no-previsto sobre la bitácora.

Lee solo las líneas nuevas desde que arranca. Cada coincidencia sale como una
línea JSON con su hora. Sale 0 si disparó al menos una vez y 1 si no disparó.
Uso: detectar_identidad.py VENTANA_SEGUNDOS [ESPERADAS]
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGLA = json.loads((ROOT / "chaos/security/detecciones/uso-credencial-no-previsto.json").read_text(encoding="utf-8"))
PATRON = re.compile(REGLA["patron"])


def evaluar(lineas: list[str]) -> list[dict]:
    alertas = []
    for linea in lineas:
        hallazgo = PATRON.match(linea.strip())
        if hallazgo and hallazgo["motivo"] in REGLA["motivos"]:
            dato = hallazgo.groupdict()
            dato["severidad"] = REGLA["severidad"].get(dato["motivo"], "media")
            alertas.append(dato)
    return alertas


def main() -> int:
    ventana = float(sys.argv[1]) if len(sys.argv) > 1 else 6
    esperadas = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    fuente = ROOT / REGLA["fuente"]
    fuente.parent.mkdir(parents=True, exist_ok=True)
    fuente.touch(exist_ok=True)
    desde = fuente.stat().st_size
    print(json.dumps({"listo": True, "t": time.time()}), flush=True)
    vistas = 0
    fin = time.time() + ventana
    while time.time() < fin:
        with fuente.open("rb") as archivo:
            archivo.seek(desde)
            nuevo = archivo.read()
        if nuevo:
            corte = nuevo.rfind(b"\n") + 1
            desde += corte
            for alerta in evaluar(nuevo[:corte].decode("utf-8", "replace").splitlines()):
                alerta["t"] = time.time()
                vistas += 1
                print(json.dumps({"alerta": REGLA["nombre"], **alerta}), flush=True)
            if esperadas and vistas >= esperadas:
                return 0
        time.sleep(REGLA["sondeo_segundos"])
    if not vistas:
        print("no disparo", flush=True)
    return 0 if vistas else 1


if __name__ == "__main__":
    raise SystemExit(main())
