#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

if [[ "$OCIR_NAMESPACE" == *"xxx"* ]] || [[ "$OCIR_AUTH_TOKEN" == PEGAR* ]] || [[ "$OCIR_USERNAME" == *"tu_usuario"* ]]; then
  echo "oci.env aún tiene valores de ejemplo (axxxxxxxxxxx / PEGAR_TOKEN / tu_usuario)."
  echo "El login de consola OCI no sirve para Docker OCIR. Completa:"
  echo "  1) Namespace: consola → Developer Services → Container Registry (Object Storage namespace)"
  echo "  2) Auth Token: Profile (arriba derecha) → User settings → Auth Tokens → Generate"
  echo "  3) OCIR_USERNAME='<namespace>/<tu-usuario>'  (si es IDCS: <namespace>/oracleidentitycloudservice/tu_email)"
  echo "  4) OCI_REGION debe coincidir con el login (home region: sa-bogota-1)"
  exit 1
fi

echo "Login OCIR ${OCI_REGION}..."
echo "$OCIR_AUTH_TOKEN" | docker login "${OCI_REGION}.ocir.io" -u "$OCIR_USERNAME" --password-stdin
echo "OK login OCIR"
