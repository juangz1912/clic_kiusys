#!/usr/bin/env bash
# Demo de alerta con un fallo en un paso del flujo multicloud.
#
#   ./scripts/demo_fallo_flujo.sh activar     # el paso api_a (POST /api/v2/mensaje) empieza a responder 500
#                                             # y se disparan FLOWS flujos por el orquestador de GCP
#   ./scripts/demo_fallo_flujo.sh desactivar  # el paso vuelve a funcionar; Pub/Sub reentrega y el flujo termina
#   ./scripts/demo_fallo_flujo.sh estado
#
# Qué se ve: el orquestador falla en el paso api_a, Pub/Sub reintenta (panel "Cola" -> reprocesados),
# la alerta "API A - errores 5xx" pasa a Firing y llega el correo. Al desactivar, el reintento pasa,
# el mensaje queda en Object Storage y la alerta se resuelve.
# Requiere DEMO_FAILURE_ENABLED=true en el ConfigMap.
set -euo pipefail
BASE_URL="${BASE_URL:-http://157-137-193-66.sslip.io}"
ORQ_URL="${ORQ_URL:-https://medical-orchestrator-400345348270.us-central1.run.app}"
FLOWS="${FLOWS:-3}"
IDS_FILE="${IDS_FILE:-/tmp/demo_fallo_flujo_ids}"

set_fallo() {
  curl -sf -X PUT -H "Content-Type: application/json" -d "{\"activo\": $1}" "$BASE_URL/api/v2/demo/fallo-flujo"
  echo
}

case "${1:-}" in
  activar)
    set_fallo true
    : > "$IDS_FILE"
    for i in $(seq 1 "$FLOWS"); do
      trace="fallo-flujo-$(date +%s)-$i"
      echo "$trace" >> "$IDS_FILE"
      code=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" \
        -H "X-Trace-Id: $trace" -d '{"resource":"imagen","id":1}' "$ORQ_URL/api/v2/flujo")
      echo "orquestador $code trace_id=$trace"
    done
    echo "El paso api_a falla y Pub/Sub reintenta. En 1-2 min la alerta pasa a Firing y llega el correo."
    ;;
  desactivar)
    set_fallo false
    echo "Pub/Sub reentrega con backoff; en unos segundos o minutos el flujo termina:"
    while read -r trace; do
      echo "  $BASE_URL/api/v2/storage/flujo/$trace"
    done < "$IDS_FILE" 2>/dev/null || true
    ;;
  estado)
    curl -sf "$BASE_URL/api/v2/demo/fallo-flujo"
    echo
    ;;
  *)
    echo "uso: $0 activar|desactivar|estado" >&2
    exit 1
    ;;
esac
