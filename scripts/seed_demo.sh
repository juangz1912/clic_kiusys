#!/usr/bin/env bash
# Siembra datos demo en un ambiente cloud o local.
# Uso: BASE_URL=https://clic-kiusys-pruebas.onrender.com ./scripts/seed_demo.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8001}"
TODAY=$(date +%Y-%m-%d)
SUFFIX=$(date +%s | tail -c 6)

echo "Sembrando datos en ${BASE_URL}..."

curl -sf -X POST "${BASE_URL}/api/vuelos" \
  -H "Content-Type: application/json" \
  -d "{\"numero_vuelo\":\"AV${SUFFIX}\",\"origen\":\"BOG\",\"destino\":\"MDE\",\"fecha\":\"${TODAY}\",\"aeronave\":\"A320\",\"capacidad\":180}" \
  | tee /tmp/vuelo.json

curl -sf -X POST "${BASE_URL}/api/pasajeros" \
  -H "Content-Type: application/json" \
  -d "{\"nombre\":\"Juan Jose Giraldo\",\"documento\":\"DOC${SUFFIX}\",\"frequent_flyer\":\"FF123\",\"tipo\":\"adulto\"}" \
  | tee /tmp/pasajero.json

VUELO_ID=$(python3 -c "import json; print(json.load(open('/tmp/vuelo.json'))['id'])")
PASAJERO_ID=$(python3 -c "import json; print(json.load(open('/tmp/pasajero.json'))['id'])")

curl -sf -X POST "${BASE_URL}/api/asientos-asignados" \
  -H "Content-Type: application/json" \
  -d "{\"vuelo_id\":${VUELO_ID},\"pasajero_id\":${PASAJERO_ID},\"fila\":12,\"columna\":\"A\",\"clase\":\"Y\",\"estado\":\"seleccionado\"}"

echo ""
echo "Listo. Vuelo=${VUELO_ID}, Pasajero=${PASAJERO_ID}"
