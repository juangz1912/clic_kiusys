from app.config import settings

TRACE_HEADER = "X-Trace-Id"


def outbound_headers(trace_id: str) -> dict[str, str]:
    return {TRACE_HEADER: trace_id, "Accept": "application/json"}
