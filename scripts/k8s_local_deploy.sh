#!/usr/bin/env bash
# Despliegue en cluster local (kind/minikube) con imágenes locales.
# Uso: CLUSTER=kind ./scripts/k8s_local_deploy.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLUSTER="${CLUSTER:-kind}"
NAMESPACE=clic-kiusys
API_IMAGE="${API_IMAGE:-clic-kiusys-api:local}"
MOCKS_IMAGE="${MOCKS_IMAGE:-clic-kiusys-mocks:local}"

echo "=== Build imágenes ==="
docker build -t "$API_IMAGE" "$ROOT"
docker build -t "$MOCKS_IMAGE" "$ROOT/companion_mocks"

if [ "$CLUSTER" = "kind" ]; then
  kind load docker-image "$API_IMAGE" "$MOCKS_IMAGE" 2>/dev/null || {
    echo "kind no encontrado o cluster no listo; usa minikube image load si aplica."
  }
fi

if [ "$CLUSTER" = "minikube" ]; then
  minikube image load "$API_IMAGE"
  minikube image load "$MOCKS_IMAGE"
fi

kubectl apply -f "$ROOT/k8s/namespace.yaml"
kubectl apply -f "$ROOT/k8s/postgres-emptydir.yaml"
kubectl apply -f "$ROOT/k8s/configmap.yaml"

kubectl -n "$NAMESPACE" create secret generic clic-kiusys-api-secret \
  --from-literal=DATABASE_URL="postgresql://pss:pss_prod@postgres:5432/pss_produccion" \
  --from-literal=API_B_BASE_URL="http://companion-mocks" \
  --from-literal=API_C_BASE_URL="http://companion-mocks" \
  --dry-run=client -o yaml | kubectl apply -f -

TMP_API="$(mktemp)"
TMP_MOCKS="$(mktemp)"
sed "s|ghcr.io/juangz1912/clic-kiusys:latest|${API_IMAGE}|g" "$ROOT/k8s/deployment.yaml" > "$TMP_API"
sed "s|ghcr.io/juangz1912/clic-kiusys-companion-mocks:latest|${MOCKS_IMAGE}|g" \
  "$ROOT/k8s/companion-mocks.yaml" > "$TMP_MOCKS"

kubectl apply -f "$TMP_MOCKS"
kubectl apply -f "$TMP_API"
kubectl apply -f "$ROOT/k8s/service.yaml"
kubectl apply -f "$ROOT/k8s/service-lb.yaml" 2>/dev/null || kubectl apply -f "$ROOT/k8s/service.yaml"
kubectl apply -f "$ROOT/k8s/hpa.yaml"

rm -f "$TMP_API" "$TMP_MOCKS"

kubectl -n "$NAMESPACE" rollout status deployment/postgres --timeout=120s
kubectl -n "$NAMESPACE" rollout status deployment/companion-mocks --timeout=120s
kubectl -n "$NAMESPACE" rollout status deployment/clic-kiusys-api --timeout=180s

echo "=== Port-forward (Ctrl+C para salir) en :8080 ==="
kubectl -n "$NAMESPACE" port-forward svc/clic-kiusys-api 8080:80 &
PF_PID=$!
sleep 3
BASE_URL=http://localhost:8080 "$ROOT/scripts/seed_demo.sh" || true
python3 "$ROOT/scripts/test_v2_endpoints.py" http://localhost:8080
kill "$PF_PID" 2>/dev/null || true
