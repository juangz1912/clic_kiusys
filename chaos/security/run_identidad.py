#!/usr/bin/env python3
"""Experimento 1: la credencial del coordinador usada fuera de lo previsto.

Ronda 0: el plano de control acepta el token estático (IDENTIDAD_ESTRICTA=false).
Ronda 1: credencial efímera con audiencia, alcance, vencimiento, origen y revocación.
Mismo método en las dos: la credencial robada se usa desde otro origen (127.0.0.2),
con un alcance que no le toca (pool) y fuera de su ventana de vida.

Uso:
  python chaos/security/run_identidad.py            corrida completa, escribe results/identidad.json
  python chaos/security/run_identidad.py --pausas   igual, pero espera Enter entre pasos (demo en vivo)
  python chaos/security/run_identidad.py --ronda 1  solo una ronda
Parada: Ctrl+C en cualquier momento. El finally revierte y apaga el API.
"""

from __future__ import annotations

import http.client
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUERTO = 8015
COORDINADOR = "127.0.0.1"
OTRO_ORIGEN = "127.0.0.2"
TOKEN_ESTATICO = "caos-local"
T1_S = 2
T2_S = 10
SECRETO = secrets.token_hex(16)

os.environ.update({"IDENTIDAD_SECRETO": SECRETO, "IDENTIDAD_ORIGENES": COORDINADOR, "IDENTIDAD_TTL_S": "60"})
sys.path.insert(0, str(ROOT))
from app.services import identidad  # noqa: E402

PAUSAS = "--pausas" in sys.argv
cronologia: list[dict] = []


def utc(t: float | None = None) -> str:
    return datetime.fromtimestamp(t or time.time(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def nota(ronda: int, hecho: str, **extra) -> dict:
    fila = {"t": utc(), "ronda": ronda, "hecho": hecho, **extra}
    cronologia.append(fila)
    print(f"[{fila['t']}] r{ronda} {hecho} " + json.dumps(extra, ensure_ascii=False))
    return fila


def paso(texto: str) -> None:
    if PAUSAS:
        input(f"\n>>> {texto}  (Enter para seguir) ")


def pedir(path: str, method: str = "GET", body: dict | None = None, token: str | None = None,
          trace: str = "-", origen: str = COORDINADOR) -> tuple[int, dict]:
    cabeceras = {"X-Trace-Id": trace}
    data = None
    if body is not None:
        data = json.dumps(body)
        cabeceras["content-type"] = "application/json"
    if token:
        cabeceras["x-chaos-token"] = token
    conexion = http.client.HTTPConnection("127.0.0.1", PUERTO, timeout=5, source_address=(origen, 0))
    try:
        conexion.request(method, path, body=data, headers=cabeceras)
        respuesta = conexion.getresponse()
        crudo = respuesta.read()
        try:
            return respuesta.status, json.loads(crudo) if crudo else {}
        except ValueError:
            return respuesta.status, {}
    except OSError as exc:
        return 0, {"error": type(exc).__name__}
    finally:
        conexion.close()


def arrancar(estricta: bool) -> subprocess.Popen:
    env = os.environ.copy()
    env.update({
        "DATABASE_URL": "sqlite:///./chaos/runtime/identidad.db",
        "ENVIRONMENT": "pruebas",
        "ADMISSION_ENABLED": "false",
        "CHAOS_TOKEN": TOKEN_ESTATICO,
        "OBJECT_STORAGE_BACKEND": "local",
        "IDENTIDAD_ESTRICTA": "true" if estricta else "false",
    })
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PUERTO),
         "--no-proxy-headers"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(80):
        if proc.poll() is not None:
            raise SystemExit("el API no arranco")
        if pedir("/api/v2/health")[0] == 200:
            return proc
        time.sleep(0.25)
    proc.kill()
    raise SystemExit("health no respondio")


def matar(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def detector(ventana: float, esperadas: int = 0) -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "chaos/security/detectar_identidad.py", str(ventana), str(esperadas)],
        cwd=ROOT, stdout=subprocess.PIPE, text=True,
    )
    proc.stdout.readline()
    return proc


def alertas_de(proc: subprocess.Popen) -> list[dict]:
    salida, _ = proc.communicate(timeout=30)
    return [json.loads(l) for l in salida.splitlines() if l.startswith("{")]


def lineas_identidad() -> int:
    ruta = ROOT / "chaos/bitacora/eventos.log"
    if not ruta.exists():
        return 0
    return sum(1 for l in ruta.read_text(encoding="utf-8").splitlines() if l.startswith("identidad "))


def parada(ronda: int) -> None:
    """Variable de parada: si el health deja de responder, se aborta y se revierte."""
    if pedir("/api/v2/health")[0] != 200:
        nota(ronda, "parada: el health no responde, se aborta")
        raise SystemExit(2)


def credenciales(ronda: int) -> dict:
    if ronda == 0:
        return {k: TOKEN_ESTATICO for k in ("leer", "telemetria", "vieja", "revocar", "revertir")}
    return {
        "leer": identidad.emitir("coordinador", "chaos:leer"),
        "telemetria": identidad.emitir("coordinador", "chaos:telemetria"),
        "vieja": identidad.emitir("coordinador", "chaos:telemetria", ttl_s=1),
        "revocar": identidad.emitir("defensor", "identidad:revocar"),
        "revertir": identidad.emitir("defensor", "chaos:revertir"),
    }


def ronda(n: int) -> dict:
    proc = arrancar(estricta=n == 1)
    cred = credenciales(n)
    resultado: dict = {"ronda": n, "control": "token estatico" if n == 0 else "credencial efimera + politica"}
    try:
        paso(f"Ronda {n}: estado estable. El coordinador lee el plano de control desde {COORDINADOR}")
        base = lineas_identidad()
        codigo, _ = pedir("/internal/chaos", token=cred["leer"], trace=f"id-r{n}-estable")
        _, latido = pedir("/internal/latido")
        nota(n, "estado estable", trace_id=f"id-r{n}-estable", status=codigo, telemetria=latido.get("telemetria"))

        paso("Caso negativo: 10 usos legitimos durante 5 s con la regla corriendo")
        neg = detector(5.0)
        legitimos = 0
        for i in range(10):
            codigo, _ = pedir("/internal/chaos", token=cred["leer"], trace=f"id-r{n}-normal-{i}")
            legitimos += codigo == 200
            time.sleep(0.5)
        falsos = len(alertas_de(neg))
        cobertura_tel = round((lineas_identidad() - base) / 11, 2)
        nota(n, "caso negativo", legitimos_200=legitimos, falsos_positivos=falsos, cobertura_telemetria=cobertura_tel)

        paso(f"Inyeccion: la credencial robada se usa desde {OTRO_ORIGEN}, con alcance de pool y vencida")
        det = detector(6.0, esperadas=3)
        usos = {}
        parada(n)
        t = time.time()
        codigo, _ = pedir("/internal/chaos", "POST", {"tipo": "telemetria", "pausada": True},
                          token=cred["telemetria"], trace=f"id-r{n}-origen", origen=OTRO_ORIGEN)
        usos["origen"] = {"t": t, "status": codigo, "trace_id": f"id-r{n}-origen"}
        nota(n, f"uso desde otro origen {OTRO_ORIGEN}", status=codigo, trace_id=f"id-r{n}-origen")

        parada(n)
        t = time.time()
        codigo, _ = pedir("/internal/chaos", "POST", {"tipo": "pool", "tamano": 1, "hold_ms": 50, "ttl_seconds": 5},
                          token=cred["telemetria"], trace=f"id-r{n}-alcance")
        usos["alcance"] = {"t": t, "status": codigo, "trace_id": f"id-r{n}-alcance"}
        nota(n, "uso con alcance no previsto (pool)", status=codigo, trace_id=f"id-r{n}-alcance")

        parada(n)
        t = time.time()
        codigo, _ = pedir("/internal/chaos", "POST", {"tipo": "telemetria", "pausada": True},
                          token=cred["vieja"], trace=f"id-r{n}-vencido")
        usos["vencido"] = {"t": t, "status": codigo, "trace_id": f"id-r{n}-vencido"}
        nota(n, "uso fuera de la ventana de vida", status=codigo, trace_id=f"id-r{n}-vencido")

        alertas = alertas_de(det)
        por_trace = {a["trace_id"]: a for a in alertas}
        mttd = {}
        for nombre, uso in usos.items():
            a = por_trace.get(uso["trace_id"])
            mttd[nombre] = round(a["t"] - uso["t"], 2) if a else None
            if a:
                nota(n, f"alerta: {a['motivo']}", trace_id=a["trace_id"], origen=a["origen"], jti=a["jti"],
                     severidad=a["severidad"], mttd_s=mttd[nombre])
        if not alertas:
            nota(n, "la regla no disparo: no hay eventos de identidad en la bitacora")
        aceptados = sum(1 for u in usos.values() if u["status"] == 200)

        paso("Contencion: revocar la credencial robada y comprobar que ya no sirve")
        primera = min((a["t"] for a in alertas), default=None)
        jti = next((a["jti"] for a in alertas if a["motivo"] == "origen"), None)
        t_c = time.time()
        codigo_rev, _ = pedir("/internal/identidad/revocar", "POST", {"jti": jti or "-"}, token=cred["revocar"],
                              trace=f"id-r{n}-contencion")
        if n == 0:
            time.sleep(max(0.0, T2_S - (time.time() - usos["origen"]["t"])))
        codigo_reuso, _ = pedir("/internal/chaos", "POST", {"tipo": "telemetria", "pausada": False},
                                token=cred["telemetria"], trace=f"id-r{n}-reuso")
        contenida = codigo_reuso in (401, 403)
        mttc = round(time.time() - (primera or t_c), 2) if contenida else None
        nota(n, "contencion", revocar_status=codigo_rev, reuso_status=codigo_reuso, contenida=contenida, mttc_s=mttc)

        paso("Reversion: telemetria encendida, pool apagado, estado inicial verificado")
        pedir("/internal/chaos", "POST", {"tipo": "off"}, token=cred["revertir"], trace=f"id-r{n}-reversion")
        pedir("/api/v2/health", trace=f"id-r{n}-final")
        _, latido = pedir("/internal/latido")
        _, estado = pedir("/internal/chaos", token=identidad.emitir("defensor", "chaos:leer") if n == 1 else TOKEN_ESTATICO)
        inicial = bool(latido.get("telemetria")) and estado.get("activo") is False
        nota(n, "reversion verificada", telemetria=latido.get("telemetria"), pool_activo=estado.get("activo"),
             estado_inicial=inicial)

        detectadas = sum(1 for v in mttd.values() if v is not None)
        resultado.update({
            "falsos_positivos": falsos,
            "usos_legitimos": legitimos,
            "cobertura_telemetria_identidad": cobertura_tel,
            "usos_adversos_aceptados": aceptados,
            "mttd_s": mttd,
            "mttd_peor_s": max((v for v in mttd.values() if v is not None), default=None),
            "mttc_s": mttc,
            "cobertura_deteccion": f"{detectadas}/3",
            "estado_inicial_verificado": inicial,
        })
        return resultado
    finally:
        pedir("/internal/chaos", "POST", {"tipo": "off"}, token=cred["revertir"], trace=f"id-r{n}-cierre")
        matar(proc)


def main() -> int:
    os.chdir(ROOT)
    (ROOT / "chaos/runtime").mkdir(parents=True, exist_ok=True)
    db = ROOT / "chaos/runtime/identidad.db"
    if db.exists():
        db.unlink()
    rondas = [int(sys.argv[sys.argv.index("--ronda") + 1])] if "--ronda" in sys.argv else [0, 1]
    inicio = utc()
    resultados = [ronda(n) for n in rondas]
    salida = {
        "experimento": 1,
        "capa": "identidad de maquinas",
        "inicio": inicio,
        "fin": utc(),
        "t1_s": T1_S,
        "t2_s": T2_S,
        "metrica_objetivo": "MTTD",
        "rondas": resultados,
        "cronologia": cronologia,
    }
    if len(rondas) == 2:
        destino = ROOT / "chaos/security/results/identidad.json"
        destino.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nescrito {destino.relative_to(ROOT)}")
    r1 = resultados[-1]
    print(json.dumps({r["ronda"]: {k: r[k] for k in ("mttd_peor_s", "mttc_s", "cobertura_deteccion", "falsos_positivos")}
                      for r in resultados}))
    ok = r1["mttd_peor_s"] is not None and r1["mttd_peor_s"] <= T1_S and r1["mttc_s"] is not None \
        and r1["mttc_s"] <= T2_S and r1["falsos_positivos"] == 0
    return 0 if ok or rondas == [0] else 1


if __name__ == "__main__":
    raise SystemExit(main())
