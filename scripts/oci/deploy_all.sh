#!/usr/bin/env bash
# Flujo completo OCI (manual): login → build/push → kubeconfig → secret → deploy → verify
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$DIR/oci.env" ]; then
  echo "Copia oci.env.example → oci.env y completa valores."
  exit 1
fi

"$DIR/01_login_ocir.sh"
"$DIR/02_build_push.sh"
"$DIR/03_kubeconfig.sh"
"$DIR/04_create_secret.sh"
"$DIR/05_deploy_oke.sh"
"$DIR/06_verify.sh"
