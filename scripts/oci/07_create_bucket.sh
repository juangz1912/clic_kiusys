#!/usr/bin/env bash
# Crea bucket OCI Object Storage (Customer Secret Key aparte en consola).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

: "${OCI_COMPARTMENT_ID:?Define OCI_COMPARTMENT_ID en oci.env}"
BUCKET="${OCI_OS_BUCKET:-clic-kiusys-flow}"

echo "Creando bucket ${BUCKET} en compartment ${OCI_COMPARTMENT_ID}..."
oci os bucket create \
  --compartment-id "$OCI_COMPARTMENT_ID" \
  --name "$BUCKET" \
  --public-access-type NoPublicAccess \
  --storage-tier Standard

echo ""
echo "Siguiente: en OCI crea Customer Secret Key (User Settings) para API S3 compatible."
echo "Copia namespace, access key y secret en oci.env:"
echo "  OCI_OS_NAMESPACE, OCI_S3_ACCESS_KEY_ID, OCI_S3_SECRET_ACCESS_KEY"
echo "Luego en k8s/configmap.yaml pon OBJECT_STORAGE_BACKEND=oci y ejecuta 04_create_secret.sh"
