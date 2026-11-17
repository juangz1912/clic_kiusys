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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8011"
TOKEN = "caos-local"
PERFIL = {
    "hilos": 12,
    "subida_s": 5,
    "sosten_s": 20,
    "bajada_s": 5,
    "timeout_s": 6,
    "p99_ms": 2000,
    "instrumento": "k6",
}
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


def k6_bin() -> str | None:
    candidato = os.environ.get("K6_BIN", "k6")
    from shutil import which

    if os.path.isfile(candidato) and os.access(candidato, os.X_OK):
        return candidato
    return which("k6")


def _cuenta(data: dict, nombre: str) -> int:
    metricas = data.get("metrics", {}).get(nombre, {}).get("values", {})
    return int(metricas.get("count", 0))


def cargar(etiqueta: str) -> dict:
    binario = k6_bin()
    if not binario:
        raise SystemExit("falta k6: el perfil fijo de las dos rondas es chaos/k6/vuelos.js")
    env = os.environ.copy()
    env["BASE_URL"] = BASE
    env["RONDA"] = etiqueta
    proc = subprocess.run(
        [binario, "run", "chaos/k6/vuelos.js"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (0, 99):
        raise SystemExit(proc.stderr[-800:] or proc.stdout[-800:])
    ruta = ROOT / "chaos" / "results" / f"k6-ronda-{etiqueta}.json"
    data = json.loads(ruta.read_text())
    dur = data["metrics"]["http_req_duration"]["values"]
    reqs = data["metrics"]["http_reqs"]["values"]
    ok = _cuenta(data, "respuestas_200")
    rechazos = _cuenta(data, "respuestas_429")
    errores = _cuenta(data, "respuestas_503") + _cuenta(data, "respuestas_otras")
    total = int(reqs.get("count", 0)) or 1
    return {
        "peticiones": int(reqs.get("count", 0)),
        "ok": ok,
        "rechazos_429": rechazos,
        "errores_5xx_o_timeout": errores,
        "por_codigo": {
            "200": ok,
            "429": rechazos,
            "503": _cuenta(data, "respuestas_503"),
            "otras": _cuenta(data, "respuestas_otras"),
        },
        "tasa_error": round(errores / total, 4),
        "throughput_rps": round(float(reqs.get("rate", 0)), 2),
        "p99_ms": round(float(dur["p(99)"]), 1),
        "p95_ms": round(float(dur.get("p(95)", 0)), 1),
        "k6_exit": proc.returncode,
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
        base = cargar(f"{nombre}-base")
        inyectar(wait_ms)
        fallo = cargar(f"{nombre}-fallo")
        revertir()
        despues = cargar(f"{nombre}-despues")
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
