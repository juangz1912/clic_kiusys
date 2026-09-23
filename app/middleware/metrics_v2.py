import re
import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_lock = Lock()
_MAX_SAMPLES = 200
_stats: dict[str, dict] = defaultdict(lambda: {"requests": 0, "errors": 0, "latency_ms_total": 0.0, "samples": []})


def route_template(path: str) -> str:
    path = re.sub(r"/[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}", "/{id}", path)
    path = re.sub(r"/\d+", "/{id}", path)
    return path


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100) * (len(ordered) - 1)))))
    return round(ordered[index], 2)


def get_v2_metrics_snapshot() -> dict[str, dict[str, float | int]]:
    with _lock:
        out: dict[str, dict[str, float | int]] = {}
        for key, val in _stats.items():
            reqs = int(val["requests"])
            avg = (val["latency_ms_total"] / reqs) if reqs else 0.0
            samples = list(val["samples"])
            out[key] = {
                "requests": reqs,
                "errors": int(val["errors"]),
                "latency_avg_ms": round(avg, 2),
                "latency_p50_ms": _percentile(samples, 50),
                "latency_p95_ms": _percentile(samples, 95),
            }
        return out


def reset_v2_metrics_for_tests() -> None:
    with _lock:
        _stats.clear()


class V2MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not path.startswith("/api/v2"):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        key = f"{request.method} {route_template(path)}"

        with _lock:
            bucket = _stats[key]
            bucket["requests"] = int(bucket["requests"]) + 1
            bucket["latency_ms_total"] = float(bucket["latency_ms_total"]) + elapsed_ms
            samples = bucket["samples"]
            samples.append(elapsed_ms)
            if len(samples) > _MAX_SAMPLES:
                del samples[: len(samples) - _MAX_SAMPLES]
            if response.status_code >= 500:
                bucket["errors"] = int(bucket["errors"]) + 1

        return response
