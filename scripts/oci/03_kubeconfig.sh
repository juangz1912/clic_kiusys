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

if [ "${OCI_CLI_AUTH:-}" = "security_token" ]; then
  KUBE_USER="$(kubectl config view --minify -o jsonpath='{.contexts[0].context.user}')"
  kubectl config set-credentials "$KUBE_USER" \
    --exec-api-version=client.authentication.k8s.io/v1beta1 \
    --exec-command="$(command -v oci)" \
    --exec-arg=ce --exec-arg=cluster --exec-arg=generate-token \
    --exec-arg=--cluster-id --exec-arg="$OKE_CLUSTER_ID" \
    --exec-arg=--region --exec-arg="$OCI_REGION" \
    --exec-env=OCI_CLI_AUTH=security_token \
    --exec-env=REQUESTS_CA_BUNDLE="${REQUESTS_CA_BUNDLE:-}"
fi

kubectl get nodes
