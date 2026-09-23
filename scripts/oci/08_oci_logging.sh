#!/usr/bin/env bash
# Log group de OCI para buscar trace_id en la consola. No falla el despliegue si falta un permiso.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

C="$OCI_COMPARTMENT_ID"
if oci logging log-group list -c "$C" --all --query "data[?\"display-name\"=='clic-kiusys'].id | [0]" --raw-output | grep -q ocid; then
  echo "Log group clic-kiusys ya existe"
  exit 0
fi
oci logging log-group create -c "$C" --display-name clic-kiusys --description "Logs API A Seguimiento 2"
echo "Log group creado. En la consola de Logging puedes buscar trace_id en los logs del contenedor cuando el agent esté activo."
