#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

kubectl apply -f "$ROOT/k8s/namespace.yaml"

DEFAULT_DB="postgresql://pss:pss_prod@postgres:5432/pss_produccion"
kubectl -n clic-kiusys create secret generic clic-kiusys-api-secret \
  --from-literal=DATABASE_URL="${DATABASE_URL:-$DEFAULT_DB}" \
  --from-literal=API_B_BASE_URL="${API_B_BASE_URL:-http://companion-mocks}" \
  --from-literal=API_C_BASE_URL="${API_C_BASE_URL:-http://companion-mocks}" \
  --from-literal=PUBLIC_API_BASE_URL="${PUBLIC_API_BASE_URL:-}" \
  --from-literal=OCI_OS_NAMESPACE="${OCI_OS_NAMESPACE:-}" \
  --from-literal=OCI_S3_ACCESS_KEY_ID="${OCI_S3_ACCESS_KEY_ID:-}" \
  --from-literal=OCI_S3_SECRET_ACCESS_KEY="${OCI_S3_SECRET_ACCESS_KEY:-}" \
  --dry-run=client -o yaml | kubectl apply -f -

if [ -n "${OCIR_AUTH_TOKEN:-}" ]; then
  kubectl -n clic-kiusys create secret docker-registry ocir-secret \
    --docker-server="${OCI_REGION}.ocir.io" \
    --docker-username="$OCIR_USERNAME" \
    --docker-password="$OCIR_AUTH_TOKEN" \
    --dry-run=client -o yaml | kubectl apply -f -
fi

echo "Secrets aplicados en namespace clic-kiusys"
