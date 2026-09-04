# Observabilidad — API A (OCI)

- **Trace-id:** header `X-Trace-Id` en requests y clientes HTTP hacia B/C.
- **Logs:** logger `clic_kiusys` con trace_id, método, path y status.
- **Métricas v2:** `GET /api/v2/metrics` (requests, errors, latencia media por endpoint).
- **OCI:** activar Logging y Monitoring del cluster OKE y workloads.
- **SaaS grupal:** enlazar tablero en `OBSERVABILITY_SAAS_URL` cuando el equipo lo configure.
