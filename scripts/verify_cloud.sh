#!/usr/bin/env bash
# Verifica endpoints clave en ambos ambientes cloud.
# Uso: ./scripts/verify_cloud.sh

set -euo pipefail

PRUEBAS_URL="${RENDER_URL_PRUEBAS:-https://clic-kiusys-pruebas.onrender.com}"
PROD_URL="${RENDER_URL_PRODUCCION:-https://clic-kiusys-prod.onrender.com}"

check_env() {
  local name="$1"
  local base="$2"

  echo "=== ${name}: ${base} ==="
  curl -sf "${base}/api/health" | python3 -m json.tool
  curl -sf -o /dev/null -w "GET /docs -> HTTP %{http_code}\n" "${base}/docs"

  local vuelo
  vuelo=$(curl -sf -X POST "${base}/api/vuelos" \
    -H "Content-Type: application/json" \
    -d '{"numero_vuelo":"TST001","origen":"BOG","destino":"CLO","fecha":"2026-08-19","aeronave":"B737","capacidad":150}')
  echo "POST /api/vuelos OK"

  local vuelo_id
  vuelo_id=$(echo "$vuelo" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

  curl -sf -X POST "${base}/api/vuelos/query" \
    -H "Content-Type: application/json" \
    -d '{"origen":"BOG"}' | python3 -m json.tool
  echo "POST /api/vuelos/query OK (vuelo_id=${vuelo_id})"
  echo ""
}

check_env "Pruebas" "$PRUEBAS_URL"
check_env "Produccion" "$PROD_URL"
echo "Verificacion cloud completada."
