# Changelog

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
