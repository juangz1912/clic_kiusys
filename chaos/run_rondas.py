#!/usr/bin/env python3
"""Mide el mismo perfil P sin proteccion y con proteccion. Escribe los JSON."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8011"
TOKEN = "caos-local"
PERFIL = {"hilos": 12, "segundos": 20, "timeout_s": 6, "p99_ms": 2000}
VUELO = {
    "numero_vuelo": "CA100",
    "origen": "BOG",
    "destino": "MDE",
    "fecha": "2026-11-18",
    "aeronave": "A320",
    "capacidad": 120,
}


def pedir(url: str, method: str = "GET", body: dict | None = None, token: bool = False, timeout: float = 6):
    data = json.dumps(body).encode() if body is not None else None
    headers = {}
    if data:
        headers["content-type"] = "application/json"
    if token:
        headers["x-chaos-token"] = TOKEN
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return exc.code, {}
    except Exception:
        return 0, {}


def percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    orden = sorted(valores)
    idx = min(len(orden) - 1, max(0, int(round((p / 100) * (len(orden) - 1)))))
    return round(orden[idx], 1)


def cargar() -> dict:
    fin = time.perf_counter() + PERFIL["segundos"]
    muestras: list[tuple[int, float]] = []

    def bucle() -> None:
        while time.perf_counter() < fin:
            t0 = time.perf_counter()
            codigo, _ = pedir(BASE + "/api/v2/entidades/vuelos/random", timeout=PERFIL["timeout_s"])
            muestras.append((codigo, (time.perf_counter() - t0) * 1000))

    with ThreadPoolExecutor(PERFIL["hilos"]) as pool:
        futuros = [pool.submit(bucle) for _ in range(PERFIL["hilos"])]
        for futuro in futuros:
            futuro.result()
    duraciones = [ms for _, ms in muestras]
    n = len(muestras) or 1
    errores = sum(1 for codigo, _ in muestras if codigo == 0 or codigo >= 500)
    rechazos = sum(1 for codigo, _ in muestras if codigo == 429)
    ok = sum(1 for codigo, _ in muestras if codigo == 200)
    por_codigo: dict[str, int] = {}
    for codigo, _ in muestras:
        clave = str(codigo)
        por_codigo[clave] = por_codigo.get(clave, 0) + 1
    return {
        "peticiones": len(muestras),
        "ok": ok,
        "rechazos_429": rechazos,
        "errores_5xx_o_timeout": errores,
        "por_codigo": por_codigo,
        "tasa_error": round(errores / n, 4),
        "throughput_rps": round(len(muestras) / PERFIL["segundos"], 2),
        "p99_ms": percentil(duraciones, 99),
        "p95_ms": percentil(duraciones, 95),
    }


def esperar_health(proc: subprocess.Popen) -> None:
    for _ in range(40):
        if proc.poll() is not None:
            raise SystemExit("el API no arranco")
        codigo, _ = pedir(BASE + "/api/v2/health", timeout=2)
        if codigo == 200:
            return
        time.sleep(0.25)
    raise SystemExit("health no respondio")


def arrancar(admision: bool) -> subprocess.Popen:
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": "sqlite:///./chaos/runtime/ronda.db",
            "ENVIRONMENT": "pruebas",
            "ADMISSION_ENABLED": "true" if admision else "false",
            "ADMISSION_MAX_INFLIGHT": "2",
            "CHAOS_TOKEN": TOKEN,
            "OBJECT_STORAGE_BACKEND": "local",
        }
    )
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8011"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def matar(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def sembrar() -> None:
    pedir(BASE + "/api/vuelos", method="POST", body=VUELO, timeout=5)


def inyectar(wait_ms: int) -> None:
    codigo, cuerpo = pedir(
        BASE + "/internal/chaos",
        method="POST",
        token=True,
        body={"tipo": "pool", "tamano": 1, "hold_ms": 700, "wait_ms": wait_ms, "ttl_seconds": 180},
    )
    if codigo != 200 or not cuerpo.get("activo"):
        raise SystemExit(f"no se activo el pool: {codigo} {cuerpo}")


def revertir() -> None:
    pedir(BASE + "/internal/chaos", method="DELETE", token=True, timeout=5)


def medir(nombre: str, admision: bool, wait_ms: int) -> dict:
    proc = arrancar(admision)
    try:
        esperar_health(proc)
        sembrar()
        base = cargar()
        inyectar(wait_ms)
        fallo = cargar()
        revertir()
        despues = cargar()
    finally:
        matar(proc)
    resultado = {
        "ronda": nombre,
        "perfil": PERFIL,
        "admision": admision,
        "sin_fallo": base,
        "con_fallo": fallo,
        "despues_de_revertir": despues,
        "hipotesis_p99": "se sostiene" if fallo["p99_ms"] < PERFIL["p99_ms"] else "se refuta",
    }
    destino = ROOT / "chaos" / "results" / f"ronda-{nombre}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultado, indent=2))
    print(json.dumps({"ronda": nombre, "con_fallo": fallo, "veredicto": resultado["hipotesis_p99"]}))
    return resultado


def main() -> int:
    if "--revertir" in sys.argv:
        revertir()
        print("revertido")
        return 0
    os.chdir(ROOT)
    (ROOT / "chaos" / "runtime").mkdir(parents=True, exist_ok=True)
    db = ROOT / "chaos" / "runtime" / "ronda.db"
    if db.exists():
        db.unlink()
    r0 = medir("0", admision=False, wait_ms=4000)
    r1 = medir("1", admision=True, wait_ms=400)
    if r0["hipotesis_p99"] != "se refuta":
        print("la ronda 0 no refuto la hipotesis", file=sys.stderr)
        return 1
    if r1["hipotesis_p99"] != "se sostiene":
        print("la ronda 1 no sostuvo la hipotesis", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
