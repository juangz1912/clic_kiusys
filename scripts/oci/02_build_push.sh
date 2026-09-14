#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

export OCIR_IMAGE="${OCI_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_REPO}:${IMAGE_TAG}"
echo "Imagen destino: $OCIR_IMAGE"

docker build -t "$OCIR_IMAGE" "$ROOT"
docker push "$OCIR_IMAGE"
echo "OCIR_IMAGE=$OCIR_IMAGE" > "$ROOT/scripts/oci/.last_image"
