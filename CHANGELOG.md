# Changelog

## v5.3.0 — 2026-11-17

- Experimento 2 de Sebastián Quintero: ruta de administración expuesta en el borde, con allowlist y rechazo del token por defecto en producción
- Experimento 4, datos del flujo: sin copia no hay recuperación; con la copia aislada el RPO fue 1,02 s y el RTO 0,0012 s

## v5.2.0 — 2026-11-17

- Experimento 1 de identidad: credencial efímera del coordinador con alcance, origen y revocación detrás de `IDENTIDAD_ESTRICTA`
- Ronda 0: 3 de 3 usos adversos aceptados y sin detección. Ronda 1: 0 de 3 aceptados, MTTD 0,25 s, MTTC 0,02 s y 0 falsos positivos
- Regla `uso-credencial-no-previsto` con caso positivo y negativo, e informe en `chaos/security/informe-identidad.md`
- `app/services/sli.py` ya no falla en Windows por el módulo `resource`
- Informe del experimento 1 con tendencias del sector (Gartner 2027, CA/B Forum SC-081v3) y versión PDF

## v5.1.1 — 2026-11-16

- Las dos rondas del pool quedaron medidas con k6 0.56.0, el mismo perfil en ambas
- Ronda 0: p99 4667,5 ms. Ronda 1: p99 40,7 ms

## v5.1.0 — 2026-11-16

- Game day de telemetría: regla de ausencia con caso negativo, MTTD 3,08 s y MTTC 0,01 s
- Señuelo, reporte con la estructura del CRA e informe de defensa distinto del de rendimiento

## v5.0.0 — 2026-11-16

- Fallo de agotamiento del pool en `GET /api/v2/entidades/vuelos/random`, con TTL y reversión
- Dos rondas con el mismo perfil: sin protección el p99 fue 4705 ms; con admisión y mamparo, 44,7 ms
- Informe del experimento en `chaos/informe-experimento.md` e informe aparte del game day de telemetría

## v4.0.0 — 2026-10-28

- api/v3 convive con api/v2. El balanceador de OCI reparte 0, 10, 50 o 100 por ciento y la cabecera `x-canary` fija el track
- Expand/Contract: columna `estado_operativo` en vuelos, visible solo en v3
- SLI por track, prueba z contra el baseline y degradación inyectable solo en el canary. Health, SLI y el interruptor quedan fuera de la falla para poder apagarla y no marcar el backend como caído
- Tablero `/tablero` con stable y canary lado a lado

## v3.0.0 — 2026-10-13

- Carpeta `terraform/`: un archivo por servicio (red, Object Storage, Autonomous Database Always Free, balanceador de 10 Mbps y VM con el API y PostgreSQL)
- Pipeline manual que aplica Terraform e instala el API, y otro que destruye la infraestructura
- `terraform/destruir.sh` para apagar todo al terminar la sustentación

## v2.3.0 — 2026-09-30

- Consumidor del Object Storage (`storage_consumer/`): Deployment propio en OKE que genera `adjuntos/<trace_id>/resumen.md` por cada mensaje del flujo, con su imagen en OCIR y su pipeline `deploy-storage-consumer.yml`
- `PUT /api/v2/demo/fallo-flujo` hace fallar el paso api_a (`POST /api/v2/mensaje`) del orquestador; `scripts/demo_fallo_flujo.sh` dispara la alerta con un fallo real del flujo
- Logs a Grafana Loki por OTLP con el trace_id de la traza (`otel_trace_id` en cada línea)
- Tablero sincronizado con las métricas de API C y del orquestador; la alerta avisa por correo a los tres integrantes
- README con el diagrama completo del grupo, los componentes transversales y la justificación de los servicios adicionales

## v2.2.1 — 2026-09-28

- Cada réplica envía sus métricas con `service.instance.id` (nombre del pod): corrige la tasa inflada y la alerta que no se resolvía
- Pipeline `deploy-oke.yml` arreglado: corre tests, build, OCIR, rollout y smoke en cada push a `main`

## v2.2.0 — 2026-09-28

- GET random por entidad: vuelos, pasajeros y asientos asignados
- `GET /api/v2/entidades/vuelos/{id}` con un Animal random de Angel (AWS) y una Imagen random de Leonardo (GCP); si un compañero falla, el vuelo igual responde
- OpenTelemetry a Grafana Cloud: trazas y métricas RED con `service.name=clic-kiusys-api`, token solo en Secret
- Tablero "Multicloud S2 - RED por API", canal de correo y alerta de errores 5xx versionados en `observability/grafana/`
- `GET /api/v2/demo/fallo` y `scripts/demo_alerta.sh` para disparar la alerta en la sustentación
- Alarma nativa de OCI Monitoring sobre CPU de los nodos de OKE (`scripts/oci/09_oci_alarm.sh`)
- Links de sustentación en el README

## v2.1.0 — 2026-09-23

- API en OKE (sa-bogota-1) con Load Balancer público
- Object Storage en bucket OCI y listado de snapshots
- POST /api/v2/mensaje agrega Vuelo, Pasajero y Asiento al mensaje del orquestador
- Integración real con Angel (AWS) y Leonardo (GCP)
- Métricas p50/p95, logs JSON, OpenTelemetry opcional y traceparent
- Pipeline deploy-oke.yml

## v2.0.0 — 2026-09-14

- API versionada `/api/v2` con health, flujo multicloud y métricas RED básicas
- Integración HTTP hacia API B de Angel (AWS) y API C de Leonardo (GCP)
- Middleware `X-Trace-Id` y logs estructurados
- Manifiestos Kubernetes/OKE (Deployment 2 réplicas, HPA, Ingress, ConfigMap, Secret)
- Workflow CI de validación de manifiestos k8s
- Documentación Seguimiento #2 y despliegue OCI

## v1.0.0 — 2026-08-19

- Seguimiento #1: API PSS v1, Docker, CI/CD Render, PostgreSQL
