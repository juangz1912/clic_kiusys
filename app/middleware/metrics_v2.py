import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_lock = Lock()
_stats: dict[str, dict[str, float | int]] = defaultdict(
    lambda: {"requests": 0, "errors": 0, "latency_ms_total": 0.0}
)


def get_v2_metrics_snapshot() -> dict[str, dict[str, float | int]]:
    with _lock:
        out: dict[str, dict[str, float | int]] = {}
        for key, val in _stats.items():
            reqs = int(val["requests"])
            avg = (val["latency_ms_total"] / reqs) if reqs else 0.0
            out[key] = {
                "requests": reqs,
                "errors": int(val["errors"]),
                "latency_avg_ms": round(avg, 2),
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
        key = f"{request.method} {path}"

        with _lock:
            bucket = _stats[key]
            bucket["requests"] = int(bucket["requests"]) + 1
            bucket["latency_ms_total"] = float(bucket["latency_ms_total"]) + elapsed_ms
            if response.status_code >= 500:
                bucket["errors"] = int(bucket["errors"]) + 1

        return response
