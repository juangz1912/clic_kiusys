#!/usr/bin/env bash
# Stack local: Postgres + mocks B/C + API + seed + smoke v2
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Levantando stack (db + mocks + api-pruebas) ==="
docker compose up -d --build db-pruebas mock-companion api-pruebas

echo "=== Esperando health API ==="
for _ in $(seq 1 30); do
  if curl -sf "http://localhost:8001/api/v2/health" >/dev/null; then
    break
  fi
  sleep 2
done

echo "=== Seed demo v1 ==="
BASE_URL=http://localhost:8001 "$ROOT/scripts/seed_demo.sh"

echo "=== Smoke v2 ==="
python3 "$ROOT/scripts/test_v2_endpoints.py" http://localhost:8001

echo ""
echo "Listo. Docs: http://localhost:8001/docs  |  v2 health: http://localhost:8001/api/v2/health"
