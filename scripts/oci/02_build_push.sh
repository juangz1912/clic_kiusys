#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

export OCIR_IMAGE="${OCI_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_REPO}:${IMAGE_TAG}"
MOCKS_REPO="${OCIR_MOCKS_REPO:-${OCIR_REPO}-mocks}"
export OCIR_MOCKS_IMAGE="${OCI_REGION}.ocir.io/${OCIR_NAMESPACE}/${MOCKS_REPO}:${IMAGE_TAG}"
echo "Imagen API: $OCIR_IMAGE"
echo "Imagen mocks: $OCIR_MOCKS_IMAGE"

docker build -t "$OCIR_IMAGE" "$ROOT"
docker build -t "$OCIR_MOCKS_IMAGE" "$ROOT/companion_mocks"
docker push "$OCIR_IMAGE"
docker push "$OCIR_MOCKS_IMAGE"
{
  echo "OCIR_IMAGE=$OCIR_IMAGE"
  echo "OCIR_MOCKS_IMAGE=$OCIR_MOCKS_IMAGE"
} > "$ROOT/scripts/oci/.last_image"
