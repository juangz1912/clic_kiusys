# Observabilidad — API A (OCI)

- **Trace-id:** `X-Trace-Id` en entrada, respuesta y clientes. También `traceparent` (W3C) en las salidas.
- **Logs:** JSON en stdout (`logger` clic_kiusys) con el mensaje que incluye `trace_id`.
- **Métricas v2:** `GET /api/v2/metrics` con requests, errors, latencia media, p50 y p95 por plantilla de ruta.
- **OpenTelemetry:** se activa solo si existe `OTEL_EXPORTER_OTLP_ENDPOINT` (listo para el SaaS del grupo).
- **OCI Logging:** log group `clic-kiusys` (script `scripts/oci/08_oci_logging.sh`).
- **SaaS grupal y alerta:** se conectan al final, cuando el equipo elija la herramienta.
