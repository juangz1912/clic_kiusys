"""OpenTelemetry. Exporta trazas, métricas y logs solo si OTEL_EXPORTER_OTLP_ENDPOINT está definido."""

import logging
import os
import socket
from urllib.parse import unquote

from fastapi import FastAPI

_duration = None
_requests = None


def _otlp_headers() -> dict[str, str]:
    raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    headers: dict[str, str] = {}
    for part in raw.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        headers[unquote(key.strip())] = unquote(value.strip())
    return headers


def _signal_url(base: str, signal: str) -> str:
    base = base.rstrip("/")
    suffix = f"/v1/{signal}"
    if base.endswith(suffix):
        return base
    return base + suffix


def record_http_request(method: str, route: str, status_code: int, elapsed_ms: float) -> None:
    if _duration is None or _requests is None:
        return
    attributes = {
        "http.method": method,
        "http.route": route,
        "http.status_code": status_code,
    }
    _requests.add(1, attributes)
    _duration.record(elapsed_ms, attributes)


def setup_telemetry(app: FastAPI) -> None:
    global _duration, _requests
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return

    from opentelemetry import metrics, trace
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    headers = _otlp_headers()
    pod = os.getenv("HOSTNAME") or socket.gethostname()
    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "clic-kiusys-api"),
            # Sin un id por réplica, los contadores de los pods se mezclan en una sola serie.
            "service.instance.id": pod,
            "k8s.pod.name": pod,
            "deployment.environment": os.getenv("ENVIRONMENT", "produccion"),
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=_signal_url(endpoint, "traces"), headers=headers)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=_signal_url(endpoint, "metrics"), headers=headers),
        export_interval_millis=15000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter("clic-kiusys")
    _requests = meter.create_counter("http.server.requests")
    _duration = meter.create_histogram("http.server.duration", unit="ms")

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=_signal_url(endpoint, "logs"), headers=headers)
        )
    )
    set_logger_provider(logger_provider)
    logging.getLogger("clic_kiusys").addHandler(
        LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    )

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
    except Exception:
        logging.getLogger("clic_kiusys").exception(
            "OpenTelemetry no pudo instrumentar FastAPI; se exportan las metricas RED igual"
        )
