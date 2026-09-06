from typing import Any

import httpx

from app.clients.http_utils import outbound_headers
from app.config import settings


def fetch_companion_entity_c(trace_id: str) -> dict[str, Any]:
    base = settings.api_c_base_url.rstrip("/")
    if not base:
        return {"source": "api_c", "configured": False, "entity": None}

    url = f"{base}{settings.api_c_entity_path}"
    try:
        with httpx.Client(timeout=settings.integration_timeout_seconds) as client:
            response = client.get(url, headers=outbound_headers(trace_id))
            response.raise_for_status()
            data = response.json()
            entity = data[0] if isinstance(data, list) and data else data
            return {"source": "api_c", "configured": True, "entity": entity, "url": url}
    except Exception as exc:
        if settings.integration_stub_when_unreachable:
            return {
                "source": "api_c",
                "configured": True,
                "entity": None,
                "error": str(exc),
                "url": url,
            }
        raise
