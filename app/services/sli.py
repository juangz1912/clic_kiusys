import resource
import time
from threading import Lock

_lock = Lock()
_samples: list[float] = []
_requests = 0
_errors_5xx = 0
_errors_4xx = 0
_estado_cambios = 0
_cpu_prev: tuple[float, float] | None = None
_MAX = 500


def registrar(status_code: int, elapsed_ms: float) -> None:
    global _requests, _errors_5xx, _errors_4xx
    with _lock:
        _requests += 1
        if status_code >= 500:
            _errors_5xx += 1
        elif status_code >= 400:
            _errors_4xx += 1
        _samples.append(elapsed_ms)
        if len(_samples) > _MAX:
            del _samples[: len(_samples) - _MAX]


def sumar_estado() -> None:
    global _estado_cambios
    with _lock:
        _estado_cambios += 1


def _percentil(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100) * (len(ordered) - 1)))))
    return round(ordered[index], 2)


def _cpu_mem() -> tuple[float, float]:
    global _cpu_prev
    uso = resource.getrusage(resource.RUSAGE_SELF)
    ahora = time.monotonic()
    cpu = uso.ru_utime + uso.ru_stime
    if _cpu_prev is None or ahora <= _cpu_prev[0]:
        _cpu_prev = (ahora, cpu)
        cpu_pct = 0.0
    else:
        cpu_pct = round(100 * (cpu - _cpu_prev[1]) / (ahora - _cpu_prev[0]), 2)
        _cpu_prev = (ahora, cpu)
    # Linux informa KB. macOS informa bytes.
    rss = uso.ru_maxrss
    mem_mb = round(rss / 1024 if rss < 10_000_000 else rss / (1024 * 1024), 2)
    return cpu_pct, mem_mb


def snapshot(version: str, track: str) -> dict:
    with _lock:
        reqs = _requests
        e5 = _errors_5xx
        e4 = _errors_4xx
        cambios = _estado_cambios
        samples = list(_samples)
    cpu, mem = _cpu_mem()
    return {
        "version": version,
        "track": track,
        "requests": reqs,
        "errors_5xx": e5,
        "errors_4xx": e4,
        "error_ratio_5xx": round(e5 / reqs, 4) if reqs else 0.0,
        "latency_p50_ms": _percentil(samples, 50),
        "latency_p95_ms": _percentil(samples, 95),
        "latency_p99_ms": _percentil(samples, 99),
        "cpu_percent": cpu,
        "memory_mb": mem,
        "estado_operativo_cambios": cambios,
    }
