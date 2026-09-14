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
fi

TMP="$(mktemp)"
sed "s|ghcr.io/juangz1912/clic-kiusys:latest|${OCIR_IMAGE}|g" "$ROOT/k8s/deployment.yaml" > "$TMP"

kubectl apply -f "$ROOT/k8s/configmap.yaml"
kubectl apply -f "$TMP"
if kubectl -n clic-kiusys get secret ocir-secret >/dev/null 2>&1; then
  kubectl -n clic-kiusys patch deployment clic-kiusys-api --type=json \
    -p='[{"op":"add","path":"/spec/template/spec/imagePullSecrets","value":[{"name":"ocir-secret"}]}]' \
    2>/dev/null || kubectl -n clic-kiusys patch deployment clic-kiusys-api --type=json \
    -p='[{"op":"replace","path":"/spec/template/spec/imagePullSecrets","value":[{"name":"ocir-secret"}]}]'
fi
kubectl apply -f "$ROOT/k8s/service.yaml"
kubectl apply -f "$ROOT/k8s/service-lb.yaml"
kubectl apply -f "$ROOT/k8s/hpa.yaml"

rm -f "$TMP"
kubectl -n clic-kiusys rollout status deployment/clic-kiusys-api --timeout=180s
kubectl -n clic-kiusys get pods,svc,hpa
