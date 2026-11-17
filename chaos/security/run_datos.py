#!/usr/bin/env python3
"""Experimento 4: borrar el objeto del flujo y medir RPO y RTO."""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from chaos.security.resguardo import CopiaAislada  # noqa: E402

OBJETO = "flujo/resumen.json"
BUENO = b'{"vuelo":"CA100","trace_id":"gd-datos","version":1}'
BASURA = b'{"borrado":true}'


def ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def preparar(base: Path) -> tuple[Path, CopiaAislada]:
    if base.exists():
        shutil.rmtree(base)
    primario = base / "primario"
    primario.mkdir(parents=True)
    return primario, CopiaAislada(base / "aislado")


def escribir(primario: Path, data: bytes) -> None:
    ruta = primario / OBJETO
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(data)


def leer(primario: Path) -> bytes | None:
    ruta = primario / OBJETO
    if not ruta.exists():
        return None
    return ruta.read_bytes()


def borrar(primario: Path) -> None:
    ruta = primario / OBJETO
    if ruta.exists():
        ruta.unlink()


def main() -> int:
    base = ROOT / "chaos" / "runtime" / "datos"
    cronologia = []

    primario, aislado = preparar(base)
    escribir(primario, BUENO)
    cronologia.append({"t": ahora(), "hecho": "estado estable", "bytes": len(BUENO)})

    # Ronda 0: no hay copia. Borrar deja el objeto irrecuperable.
    borrar(primario)
    t0 = time.perf_counter()
    try:
        aislado.leer(OBJETO)
        recuperado_0 = True
    except FileNotFoundError:
        recuperado_0 = False
    rto_0 = round(time.perf_counter() - t0, 4)
    cronologia.append({
        "t": ahora(),
        "hecho": "ronda 0: objeto borrado, sin copia",
        "recuperado": recuperado_0,
        "rpo_s": None,
        "rto_s": None if not recuperado_0 else rto_0,
    })

    # Ronda 1: la copia se toma al escribir. El borrado no la toca.
    primario, aislado = preparar(base)
    marca_buena = time.perf_counter()
    escribir(primario, BUENO)
    aislado.guardar(OBJETO, BUENO)
    time.sleep(1.0)
    incidente = time.perf_counter()
    escribir(primario, BASURA)
    borrar(primario)
    cronologia.append({"t": ahora(), "hecho": "ronda 1: primario borrado, copia intacta"})
    t_rest = time.perf_counter()
    restaurado = aislado.leer(OBJETO)
    escribir(primario, restaurado)
    rto_1 = round(time.perf_counter() - t_rest, 4)
    rpo_1 = round(incidente - marca_buena, 3)
    try:
        aislado.borrar(OBJETO)
        copia_borrable = True
    except PermissionError:
        copia_borrable = False
    cronologia.append({
        "t": ahora(),
        "hecho": "ronda 1: restaurado desde la copia aislada",
        "igual_al_original": leer(primario) == BUENO,
        "copia_borrable": copia_borrable,
        "rpo_s": rpo_1,
        "rto_s": rto_1,
    })

    resultado = {
        "fecha": ahora(),
        "rpo_objetivo_s": 5,
        "rto_objetivo_s": 2,
        "ronda_0": {"recuperado": recuperado_0, "rpo_s": None, "rto_s": None, "hipotesis": "se refuta"},
        "ronda_1": {
            "recuperado": leer(primario) == BUENO,
            "rpo_s": rpo_1,
            "rto_s": rto_1,
            "copia_borrable": copia_borrable,
            "hipotesis": "se sostiene" if rpo_1 <= 5 and rto_1 <= 2 and leer(primario) == BUENO else "se refuta",
        },
        "cronologia": cronologia,
    }
    destino = ROOT / "chaos" / "security" / "results" / "datos.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(json.dumps({"rpo_s": rpo_1, "rto_s": rto_1, "ronda_0": recuperado_0, "veredicto": resultado["ronda_1"]["hipotesis"]}))
    shutil.rmtree(base, ignore_errors=True)
    return 0 if resultado["ronda_1"]["hipotesis"] == "se sostiene" and not recuperado_0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
