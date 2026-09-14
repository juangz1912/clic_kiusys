#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== Pods / HPA ==="
kubectl -n clic-kiusys get pods -o wide
kubectl -n clic-kiusys get hpa

echo ""
echo "=== LoadBalancer (URL pública OCI) ==="
kubectl -n clic-kiusys get svc clic-kiusys-api-lb -o wide

LB_HOST=$(kubectl -n clic-kiusys get svc clic-kiusys-api-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)
if [ -z "$LB_HOST" ]; then
  LB_HOST=$(kubectl -n clic-kiusys get svc clic-kiusys-api-lb -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
fi

if [ -n "$LB_HOST" ]; then
  BASE="http://${LB_HOST}"
  echo "Sembrando datos demo en ${BASE} ..."
  BASE_URL="$BASE" "$ROOT/scripts/seed_demo.sh" || true
  echo "Probando v2 en ${BASE} ..."
  python3 "$ROOT/scripts/test_v2_endpoints.py" "$BASE" || true
else
  echo "El LoadBalancer aún no tiene IP/hostname (espera 2-5 min y vuelve a ejecutar)."
fi
