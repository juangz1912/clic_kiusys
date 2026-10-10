#!/bin/bash
# Sube terraform.tfstate al bucket privado para que el pipeline pueda seguir desde ahí.
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
source ./env.sh
export PATH="$HOME/.local/bin:/usr/bin:/bin:/usr/local/bin:$HOME/Library/Python/3.12/bin:$PATH"
export REQUESTS_CA_BUNDLE="${REQUESTS_CA_BUNDLE:-$HOME/.oci/ca-bundle.pem}"

bucket="$(terraform output -raw tfstate_bucket)"
oci os object put \
  --bucket-name "$bucket" \
  --name terraform.tfstate \
  --file terraform.tfstate \
  --force \
  --content-type application/json >/dev/null
echo "Estado guardado en $bucket/terraform.tfstate"
