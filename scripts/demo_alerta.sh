#!/usr/bin/env bash
# Provoca respuestas 500 en la API para que la alerta de Grafana "API A - errores 5xx" se dispare.
# Requiere DEMO_FAILURE_ENABLED=true en el ConfigMap.
set -euo pipefail
BASE_URL="${BASE_URL:-http://157-137-193-66.sslip.io}"
REQUESTS="${REQUESTS:-30}"

echo "Provocando $REQUESTS fallos en $BASE_URL/api/v2/demo/fallo"
for i in $(seq 1 "$REQUESTS"); do
  trace="alerta-demo-$(date +%s)-$i"
  code=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Trace-Id: $trace" "$BASE_URL/api/v2/demo/fallo")
  echo "$code trace_id=$trace"
  sleep 2
done
echo "La alerta pasa a Firing en 1-2 min y llega el correo. Se resuelve sola al dejar de provocar fallos."
