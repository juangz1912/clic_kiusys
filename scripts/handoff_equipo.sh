#!/usr/bin/env bash
# Imprime mensaje listo para el chat del equipo (Integrante A / OCI).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

BASE="${PUBLIC_API_BASE_URL:-http://localhost:8001}"
BASE="${1:-$BASE}"

cat <<EOF
=== Seguimiento #2 — Integrante A (Oracle OCI) ===

Repo API A + Object Storage consumidor:
  https://github.com/juangz1912/clic_kiusys

URL base API A (OKE / pruebas):
  ${BASE}

Nube: Oracle OCI (OKE + Object Storage bucket: clic-kiusys-flow)

--- Endpoints v2 (invocar con header X-Trace-Id) ---
  GET  ${BASE}/api/v2/health
  POST ${BASE}/api/v2/flujo
  GET  ${BASE}/api/v2/metrics

--- Consumir entidad local (Vuelo) desde vuestra API v2 ---
  GET  ${BASE}/api/v2/entidades/vuelos
  (alternativa v1: GET ${BASE}/api/vuelos)

--- Object Storage (JSON acumulado del flujo + adjuntos) ---
  Tras POST /api/v2/flujo la respuesta trae object_storage.get_url
  GET  ${BASE}/api/v2/storage/flujo/{trace_id}
  POST ${BASE}/api/v2/storage/adjunto  (multipart, header X-Trace-Id)
  GET  ${BASE}/api/v2/storage/adjunto/{trace_id}/{filename}

--- Necesito de ustedes ---
  Integrante B (GCP): URL base + path GET lista (ej. /api/mascotas)
  Integrante C (Azure/AWS): URL base + path GET lista (ej. /api/items)
  URLs publicas (no localhost). Mismo header X-Trace-Id en toda la cadena.

--- Roles transversales (confirmen reparto) ---
  MS orquestador | Cola/DLQ | Cache | (Object Storage = yo en OCI)

--- Prueba rapida ---
  curl -s ${BASE}/api/v2/health -H "X-Trace-Id: demo-1"
  curl -s -X POST ${BASE}/api/v2/flujo -H "Content-Type: application/json" -H "X-Trace-Id: demo-1" -d '{}'

EOF
