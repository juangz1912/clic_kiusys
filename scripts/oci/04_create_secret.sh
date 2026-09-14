#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

kubectl apply -f "$ROOT/k8s/namespace.yaml"

kubectl -n clic-kiusys create secret generic clic-kiusys-api-secret \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --from-literal=API_B_BASE_URL="${API_B_BASE_URL:-}" \
  --from-literal=API_C_BASE_URL="${API_C_BASE_URL:-}" \
  --dry-run=client -o yaml | kubectl apply -f -

if [ -n "${OCIR_AUTH_TOKEN:-}" ]; then
  kubectl -n clic-kiusys create secret docker-registry ocir-secret \
    --docker-server="${OCI_REGION}.ocir.io" \
    --docker-username="$OCIR_USERNAME" \
    --docker-password="$OCIR_AUTH_TOKEN" \
    --dry-run=client -o yaml | kubectl apply -f -
fi

echo "Secrets aplicados en namespace clic-kiusys"
