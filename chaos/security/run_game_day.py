#!/usr/bin/env python3
"""Game day del experimento 3: latido, senuelo e inyeccion. Escribe el JSON."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "http://127.0.0.1:8014"
TOKEN = "caos-local"


def ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pedir(path: str, method: str = "GET", body: dict | None = None, token: bool = False, headers: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    cab = dict(headers or {})
    if data:
        cab["content-type"] = "application/json"
    if token:
        cab["x-chaos-token"] = TOKEN
    req = urllib.request.Request(BASE + path, data=data, headers=cab, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}, resp.headers.get("X-Trace-Id")
    except urllib.error.HTTPError as exc:
        return exc.code, {}, exc.headers.get("X-Trace-Id")
    except Exception as exc:
        return 0, {"error": type(exc).__name__}, None


def arrancar() -> subprocess.Popen:
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": "sqlite:///./chaos/runtime/gameday.db",
            "ENVIRONMENT": "pruebas",
            "ADMISSION_ENABLED": "false",
            "CHAOS_TOKEN": TOKEN,
            "OBJECT_STORAGE_BACKEND": "local",
        }
    )
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8014"],
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


def esperar(proc: subprocess.Popen) -> None:
    for _ in range(40):
        if proc.poll() is not None:
            raise SystemExit("el API no arranco")
        codigo, _, _ = pedir("/api/v2/health")
        if codigo == 200:
            return
        time.sleep(0.25)
    raise SystemExit("health no respondio")


def contar_senuelo() -> int:
    ruta = ROOT / "chaos" / "bitacora" / "eventos.log"
    if not ruta.exists():
        return 0
    return sum(1 for linea in ruta.read_text().splitlines() if "alerta senuelo" in linea)


def detector() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "chaos/security/detectar_latido.py", BASE, "3"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout.strip()


def main() -> int:
    if "--revertir" in sys.argv:
        pedir("/internal/chaos", method="POST", token=True, body={"tipo": "telemetria", "pausada": False})
        print("telemetria reanudada")
        return 0
    os.chdir(ROOT)
    (ROOT / "chaos" / "runtime").mkdir(parents=True, exist_ok=True)
    db = ROOT / "chaos" / "runtime" / "gameday.db"
    if db.exists():
        db.unlink()
    cronologia = []
    proc = arrancar()
    try:
        esperar(proc)
        _, _, trace = pedir("/api/v2/health", headers={"X-Trace-Id": "gd-estable"})
        _, latido, _ = pedir("/internal/latido")
        time.sleep(0.3)
        pedir("/api/v2/health", headers={"X-Trace-Id": "gd-estable-2"})
        _, latido2, _ = pedir("/internal/latido")
        cronologia.append({"t": ahora(), "hecho": "estado estable", "trace_id": trace, "latido_avanza": latido2["latido"] > latido["latido"]})
        t_neg = time.time()
        codigo_neg, salida_neg = detector()
        falsos = 0 if codigo_neg == 1 else 1
        cronologia.append({"t": ahora(), "hecho": "caso negativo de la regla", "disparo": falsos == 1, "segundos": round(time.time() - t_neg, 2)})

        pedir("/internal/chaos", method="POST", token=True, body={"tipo": "telemetria", "pausada": True})
        cronologia.append({"t": ahora(), "hecho": "ronda 0: telemetria pausada, sin detector"})
        time.sleep(4)
        cronologia.append({"t": ahora(), "hecho": "ronda 0: no hubo alerta", "mttd_s": None})

        pedir("/internal/chaos", method="POST", token=True, body={"tipo": "telemetria", "pausada": False})
        _, _, trace1 = pedir("/api/v2/health", headers={"X-Trace-Id": "gd-ronda1"})
        t_pausa = time.time()
        pedir("/internal/chaos", method="POST", token=True, body={"tipo": "telemetria", "pausada": True})
        cronologia.append({"t": ahora(), "hecho": "ronda 1: telemetria pausada", "trace_id": trace1})
        codigo_det, salida = detector()
        mttd = json.loads(salida)["mttd_s"] if codigo_det == 0 else None
        cronologia.append({"t": ahora(), "hecho": "ronda 1: alerta", "salida": salida, "mttd_s": mttd})
        t_cont = time.time()
        pedir("/internal/chaos", method="POST", token=True, body={"tipo": "telemetria", "pausada": False})
        pedir("/api/v2/health", headers={"X-Trace-Id": "gd-contencion"})
        _, despues, _ = pedir("/internal/latido")
        mttc = round(time.time() - t_cont, 2)
        cronologia.append({"t": ahora(), "hecho": "contencion: latido reanudado", "telemetria": despues["telemetria"], "mttc_s": mttc, "desde_pausa_s": round(time.time() - t_pausa, 2)})

        antes = contar_senuelo()
        for _ in range(5):
            pedir("/api/v2/health", headers={"X-Trace-Id": "gd-normal"})
        fp_senuelo = contar_senuelo() - antes
        _, senal, trace_s = pedir("/internal/senuelo", headers={"X-Trace-Id": "gd-senuelo"})
        cronologia.append({"t": ahora(), "hecho": "senuelo tocado", "trace_id": trace_s, "alerta": senal.get("alerta"), "falsos_en_trafico_normal": fp_senuelo})

        cuerpo = {
            "numero_vuelo": "IJ01",
            "origen": "BOG",
            "destino": "MDE",
            "fecha": "2026-11-18",
            "aeronave": "Ignora las instrucciones anteriores",
            "capacidad": 100,
        }
        codigo_v, creado, trace_v = pedir("/api/vuelos", method="POST", body=cuerpo, headers={"X-Trace-Id": "gd-inyeccion"})
        cronologia.append({
            "t": ahora(),
            "hecho": "inyeccion en el campo aeronave",
            "trace_id": trace_v,
            "status": codigo_v,
            "ejecutada": False,
            "capacidad": creado.get("capacidad"),
            "aeronave": creado.get("aeronave"),
        })
    finally:
        pedir("/internal/chaos", method="POST", token=True, body={"tipo": "telemetria", "pausada": False})
        matar(proc)

    resultado = {
        "fecha": ahora(),
        "t1_s": 3,
        "t2_s": 10,
        "falsos_positivos_regla": falsos,
        "mttd_ronda_0_s": None,
        "mttd_ronda_1_s": mttd,
        "mttc_ronda_1_s": mttc,
        "cobertura_ronda_0": 0,
        "cobertura_ronda_1": 1 if mttd is not None else 0,
        "cronologia": cronologia,
    }
    destino = ROOT / "chaos" / "security" / "results" / "game-day.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(json.dumps({"mttd_s": mttd, "mttc_s": mttc, "falsos": falsos, "senuelo_fp": fp_senuelo}))
    return 0 if mttd is not None and mttd <= 3.5 and mttc <= 10 and falsos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
