#!/bin/bash
# Fija el porcentaje público del canary: 0, 10, 50 o 100.
set -euo pipefail
porcentaje="${1:?uso: peso.sh 0|10|50|100}"
case "$porcentaje" in
  0|10|50|100) ;;
  *) echo "porcentaje inválido" >&2; exit 1 ;;
esac
if [ "${CANARY_BACKEND:-oci}" = "compose" ]; then
  exec "$(dirname "$0")/peso_compose.sh" "$porcentaje"
fi
cd "$(dirname "$0")/../terraform"
# shellcheck disable=SC1091
source ./env.sh
export PATH="$HOME/.local/bin:$PATH"
terraform apply -input=false -auto-approve -var "canary_percent=${porcentaje}"
echo "canary_percent=${porcentaje}"
