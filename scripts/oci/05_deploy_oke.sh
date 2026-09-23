#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

if [ -f "$ROOT/scripts/oci/.last_image" ]; then
  # shellcheck source=/dev/null
  source "$ROOT/scripts/oci/.last_image"
else
  export OCIR_IMAGE="${OCI_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_REPO}:${IMAGE_TAG}"
  MOCKS_REPO="${OCIR_MOCKS_REPO:-${OCIR_REPO}-mocks}"
  export OCIR_MOCKS_IMAGE="${OCI_REGION}.ocir.io/${OCIR_NAMESPACE}/${MOCKS_REPO}:${IMAGE_TAG}"
fi
OCIR_MOCKS_IMAGE="${OCIR_MOCKS_IMAGE:-${OCI_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_MOCKS_REPO:-${OCIR_REPO}-mocks}:${IMAGE_TAG}}"

TMP_API="$(mktemp)"
TMP_MOCKS="$(mktemp)"
sed "s|ghcr.io/juangz1912/clic-kiusys:latest|${OCIR_IMAGE}|g" "$ROOT/k8s/deployment.yaml" > "$TMP_API"
sed "s|ghcr.io/juangz1912/clic-kiusys-companion-mocks:latest|${OCIR_MOCKS_IMAGE}|g" \
  "$ROOT/k8s/companion-mocks.yaml" > "$TMP_MOCKS"

kubectl apply -f "$ROOT/k8s/postgres.yaml"
kubectl -n clic-kiusys rollout status deployment/postgres --timeout=300s || true

kubectl apply -f "$ROOT/k8s/configmap.yaml"
kubectl apply -f "$TMP_MOCKS"
kubectl apply -f "$TMP_API"
if kubectl -n clic-kiusys get secret ocir-secret >/dev/null 2>&1; then
  for dep in clic-kiusys-api companion-mocks; do
    kubectl -n clic-kiusys patch deployment "$dep" --type=json \
      -p='[{"op":"add","path":"/spec/template/spec/imagePullSecrets","value":[{"name":"ocir-secret"}]}]' \
      2>/dev/null || kubectl -n clic-kiusys patch deployment "$dep" --type=json \
      -p='[{"op":"replace","path":"/spec/template/spec/imagePullSecrets","value":[{"name":"ocir-secret"}]}]'
  done
fi
kubectl apply -f "$ROOT/k8s/service.yaml"
kubectl apply -f "$ROOT/k8s/service-lb.yaml"

# OKE no trae metrics-server; sin él el HPA queda en <unknown>
if ! kubectl -n kube-system get deployment metrics-server >/dev/null 2>&1; then
  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
fi
kubectl apply -f "$ROOT/k8s/hpa.yaml"

rm -f "$TMP_API" "$TMP_MOCKS"
kubectl -n clic-kiusys rollout status deployment/companion-mocks --timeout=120s
kubectl -n clic-kiusys rollout status deployment/clic-kiusys-api --timeout=180s
kubectl -n clic-kiusys get pods,svc,hpa
