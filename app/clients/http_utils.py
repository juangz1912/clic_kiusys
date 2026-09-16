from typing import Any

import httpx

from app.config import settings

TRACE_HEADER = "X-Trace-Id"


def outbound_headers(trace_id: str) -> dict[str, str]:
    return {TRACE_HEADER: trace_id, "Accept": "application/json"}


def unwrap_entity(data: Any) -> Any:
    if isinstance(data, dict) and "data" in data:
        inner = data["data"]
        if isinstance(inner, list):
            return inner[0] if inner else None
        return inner
    if isinstance(data, list):
        return data[0] if data else None
    return data


def fetch_remote_entity(
    source: str,
    base_url: str,
    path: str,
    trace_id: str,
) -> dict[str, Any]:
    base = (base_url or "").rstrip("/")
    if not base:
        return {"source": source, "configured": False, "entity": None, "url": None}

    url = f"{base}{path}"
    try:
        with httpx.Client(timeout=settings.integration_timeout_seconds) as client:
            response = client.get(url, headers=outbound_headers(trace_id))
            response.raise_for_status()
            return {
                "source": source,
                "configured": True,
                "entity": unwrap_entity(response.json()),
                "url": url,
            }
    except Exception as exc:
        if settings.integration_stub_when_unreachable:
            return {
                "source": source,
                "configured": True,
                "entity": None,
                "error": str(exc),
                "url": url,
            }
        raise
