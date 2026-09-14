#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

if ! command -v oci >/dev/null 2>&1; then
  echo "Instala OCI CLI: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm"
  exit 1
fi

oci ce cluster create-kubeconfig \
  --cluster-id "$OKE_CLUSTER_ID" \
  --file "$HOME/.kube/config" \
  --region "$OCI_REGION" \
  --token-version 2.0.0 \
  --kube-endpoint PUBLIC_ENDPOINT

kubectl config use-context "${KUBECONFIG_CONTEXT:-$(kubectl config current-context)}"
kubectl get nodes
