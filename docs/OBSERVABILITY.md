# Observabilidad — API A (OCI) y capa de métricas del grupo

## Lo que emite la API

- **Trace-id:** `X-Trace-Id` en entrada, respuesta y clientes. También `traceparent` (W3C) en las salidas.
- **Logs:** JSON en stdout (`logger` clic_kiusys) con `trace_id` (el `X-Trace-Id`), `otel_trace_id` (el de la traza W3C), método, ruta y status. Con OTLP activo también van a Loki.
- **Métricas v2 del pod:** `GET /api/v2/metrics` con requests, errors, latencia media, p50 y p95 por ruta. Son por réplica: con 2 pods cada llamada puede caer en uno distinto.
- **OpenTelemetry:** si existe `OTEL_EXPORTER_OTLP_ENDPOINT`, exporta trazas, logs y métricas (cada 15 s) a Grafana Cloud:
  - `http_server_requests_total{service_name, http_method, http_route, http_status_code}`
  - `http_server_duration_milliseconds_bucket{...}` (histograma para p50/p95)
  - trazas de FastAPI y de las llamadas httpx a Angel y Leonardo

`http_route` es la plantilla de FastAPI (`/api/v2/entidades/vuelos/{vuelo_id}`); lo que no coincide con ninguna ruta queda como `sin_ruta`.

## Grafana Cloud (SaaS del grupo)

- Stack: https://browngecko19.grafana.net (región prod-us-east-3)
- Tablero: [Multicloud S2 - RED por API](https://browngecko19.grafana.net/d/clic-s2-red/multicloud-s2-red-por-api), en la carpeta "Multicloud S2"
- Alerta: **API A - errores 5xx en api/v2**. Se dispara si hay más de 0 respuestas 5xx en 2 minutos, evalúa cada 30 s, pendiente 30 s y avisa por correo (`clic-s2-email`).
- Todo está versionado en `observability/grafana/` y se aplica con:

```bash
GRAFANA_URL=https://browngecko19.grafana.net GRAFANA_TOKEN=glsa_... python3 scripts/grafana_apply.py
```

El token OTLP (envío) vive solo en el Secret `grafana-otlp` del cluster. El token `glsa_` (administración) no se guarda en ningún lado.

### Cómo se suman Angel y Leonardo

Cada API exporta OpenTelemetry al mismo stack con su propio nombre:

| API | `OTEL_SERVICE_NAME` |
|-----|---------------------|
| API A (OCI) | `clic-kiusys-api` |
| API B (AWS) | `api-b-adopcion` |
| API C (GCP) | `api-c-documentos` |
| Orquestador (GCP, Cloud Run) | `medical-orchestrator` |

Variables comunes: `OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-3.grafana.net/otlp`, `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf` y `OTEL_EXPORTER_OTLP_HEADERS` (se pasa por privado y va en un Secret). Deben usar las mismas métricas (`http.server.requests` y `http.server.duration` en ms, con `http.route` y `http.status_code`) para que el tablero las muestre sin cambios. Si reenvían `traceparent`, una traza cruza las tres nubes.

### Logs de las tres nubes por trace_id

El identificador común es el trace_id W3C de OpenTelemetry: viaja en `traceparent` de OCI a AWS y a GCP, y una misma traza de Tempo muestra spans de `clic-kiusys-api`, `api-b-adopcion` y `api-c-documentos`. Cada API manda sus logs por OTLP (`/v1/logs`, mismo endpoint y header) y Loki guarda `trace_id` y `span_id` en cada línea.

Para reconstruir el recorrido de un mensaje:

1. Hacer la petición y tomar el trace_id: `GET /api/v2/entidades/vuelos/1` y buscar la traza en Explore → Tempo (`{resource.service.name="clic-kiusys-api"}`), o leer `otel_trace_id` en el log.
2. En Explore → Loki:

```logql
{service_name=~"clic-kiusys-api|api-b-adopcion|api-c-documentos|medical-orchestrator"} | trace_id="<trace_id>"
```

Salen las líneas de los tres proveedores ordenadas por tiempo. Desde un span en Tempo, "Logs for this span" hace la misma consulta.

Caché y cola: el tablero espera `cache_hits_total` y `cache_misses_total` de la caché Redis de Angel (el panel usa `max` porque cada pod reporta el mismo total de Redis) y `queue_messages_pending` y `queue_messages_reprocessed_total` del orquestador de Leonardo (Pub/Sub).

## OCI nativo

- **Monitoring:** alarma `clic-kiusys-oke-cpu-alta`, `CpuUtilization` de los nodos de OKE > 80 % durante 1 min, avisa al topic `clic-kiusys-alertas` por correo (`scripts/oci/09_oci_alarm.sh`). La carga de `scripts/k8s_hpa_demo.sh` la puede disparar.
- **Logging:** log group `clic-kiusys` (`scripts/oci/08_oci_logging.sh`). Para buscar un trace_id en los pods:

```bash
kubectl -n clic-kiusys logs -l app=clic-kiusys-api --since=10m | grep sustentacion-1
```

## Demo de alerta

1. `./scripts/demo_alerta.sh` hace 30 llamadas a `/api/v2/demo/fallo` (una cada 2 s), cada una con su trace_id.
2. En 1 a 2 minutos la alerta pasa de Normal a Pending y luego a Firing, y llega el correo.
3. En el tablero se ve el pico en "Errors" y en "% errores 5xx".
4. Al dejar de provocar fallos, la alerta vuelve a Normal y llega el correo de resuelta.
