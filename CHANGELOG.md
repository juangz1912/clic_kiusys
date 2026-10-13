# Changelog

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
