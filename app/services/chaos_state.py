"""Interruptor del experimento de agotamiento del pool.

Apagado por defecto. El TTL lo revierte solo. No toca filas de la base.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

_lock = threading.Lock()
_pool = threading.BoundedSemaphore(32)
_pool_size = 32
_hold_ms = 0
_wait_ms = 4000
_deadline = 0.0
_active = False
_telemetry = True
_last_beat = time.time()
_rejected = 0
_waited = 0
_inflight = 0
_inflight_lock = threading.Lock()


def _rebuild(size: int) -> None:
    global _pool, _pool_size
    _pool_size = max(1, size)
    _pool = threading.BoundedSemaphore(_pool_size)


def estado() -> dict:
    with _lock:
        activo = _active and (_deadline == 0 or time.time() < _deadline)
        return {
            "activo": activo,
            "pool_size": _pool_size if activo else None,
            "hold_ms": _hold_ms if activo else 0,
            "segundos_restantes": max(0, int(_deadline - time.time())) if activo and _deadline else 0,
            "telemetria": _telemetry,
            "rechazadas": _rejected,
            "en_espera": _waited,
            "latido": _last_beat,
        }


def activar_pool(tamano: int, hold_ms: int, ttl_seconds: int, wait_ms: int) -> dict:
    global _hold_ms, _wait_ms, _deadline, _active
    with _lock:
        _rebuild(tamano)
        _hold_ms = hold_ms
        _wait_ms = wait_ms
        _deadline = time.time() + ttl_seconds
        _active = True
    return estado()


def apagar() -> dict:
    global _active, _deadline, _hold_ms, _telemetry
    with _lock:
        _active = False
        _deadline = 0
        _hold_ms = 0
        _telemetry = True
        _rebuild(32)
    return estado()


def pausar_telemetria(pausada: bool) -> dict:
    global _telemetry
    with _lock:
        _telemetry = not pausada
    return estado()


def latido(path: Path | None = None) -> None:
    global _last_beat
    if not _telemetry:
        return
    _last_beat = time.time()
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(_last_beat))


def adquirir() -> str:
    """Devuelve ok, rechazada o agotada. El llamador suelta el cupo con soltar()."""
    global _rejected, _waited
    ahora = time.time()
    with _lock:
        if not _active or (_deadline and ahora >= _deadline):
            return "libre"
        espera = _wait_ms / 1000
        hold = _hold_ms / 1000
    if not _pool.acquire(timeout=espera):
        with _lock:
            _rejected += 1
        return "agotada"
    if hold:
        time.sleep(hold)
        with _lock:
            _waited += 1
    return "ok"


def soltar(resultado: str) -> None:
    if resultado == "ok":
        try:
            _pool.release()
        except ValueError:
            return


def entrar_admision(maximo: int) -> bool:
    global _inflight
    with _inflight_lock:
        if _inflight >= maximo:
            return False
        _inflight += 1
        return True


def salir_admision() -> None:
    global _inflight
    with _inflight_lock:
        _inflight = max(0, _inflight - 1)


def sumar_rechazo_admision() -> None:
    global _rejected
    with _lock:
        _rejected += 1
