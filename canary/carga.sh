#!/bin/bash
# Manda la misma cantidad de peticiones a stable y a canary, fijando el track con la cabecera.
set -euo pipefail
base="${1:-http://127.0.0.1}"
n="${2:-50}"
for i in $(seq 1 "$n"); do
  curl -sS -o /dev/null -H 'x-canary: false' "$base/api/v2/entidades/vuelos" || true &
  curl -sS -o /dev/null -H 'x-canary: true' "$base/api/v2/entidades/vuelos" || true &
  if (( i % 10 == 0 )); then
    wait
  fi
done
wait
echo "listo: $n a cada track"
