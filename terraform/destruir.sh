#!/bin/bash
# Elimina toda la infraestructura de este directorio. Correrlo al terminar la sustentación.
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
source ./env.sh
export PATH="$HOME/.local/bin:$PATH"

if [[ ! -f terraform.tfstate ]]; then
  export REQUESTS_CA_BUNDLE="${REQUESTS_CA_BUNDLE:-$HOME/.oci/ca-bundle.pem}"
  export PATH="/usr/bin:/bin:/usr/local/bin:$HOME/Library/Python/3.12/bin:$PATH"
  oci os object get \
    --bucket-name clic-kiusys-tfstate \
    --name terraform.tfstate \
    --file terraform.tfstate || true
fi

terraform init -input=false
terraform destroy -auto-approve -input=false
echo "Infraestructura eliminada."
