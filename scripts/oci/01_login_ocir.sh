#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

echo "Login OCIR ${OCI_REGION}..."
echo "$OCIR_AUTH_TOKEN" | docker login "${OCI_REGION}.ocir.io" -u "$OCIR_USERNAME" --password-stdin
echo "OK login OCIR"
