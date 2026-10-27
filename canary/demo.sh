#!/bin/bash
# Recorre las cuatro pruebas en vivo del canary y deja la evidencia en canary/evidencias/.
set -euo pipefail

base="${1:?uso: demo.sh http://IP}"
base="${base%/}"
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/canary/evidencias"
mkdir -p "$out"
log="$out/ejecucion.md"

track() {
  curl -sD - -o /dev/null --max-time 8 "$@" | awk 'BEGIN{IGNORECASE=1} /^x-app-track:/{gsub(/\r/,""); print $2}'
}

contar() {
  local n="$1" s=0 c=0 otro=0 t
  for _ in $(seq 1 "$n"); do
    t="$(track "$base/api/v2/health")"
    case "$t" in
      stable) s=$((s + 1)) ;;
      canary) c=$((c + 1)) ;;
      *) otro=$((otro + 1)) ;;
    esac
  done
  echo "stable=$s canary=$c otros=$otro de $n"
}

{
  echo "# Evidencia canary $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "Base: $base"
  echo
  echo "## Etapa 0: el público cae en stable y la cabecera entra al canary"
  echo
  echo '```'
  echo -n "sin cabecera: "; track "$base/api/v2/health"
  echo -n "x-canary false: "; track -H 'x-canary: false' "$base/api/v2/health"
  echo -n "x-canary true: "; track -H 'x-canary: true' "$base/api/v2/health"
  echo '```'
} | tee "$log"

echo "Muestra sana, 50 por track" | tee -a "$log"
bash "$root/canary/carga.sh" "$base" 50 | tee -a "$log"
echo '```' | tee -a "$log"
python3 "$root/canary/evaluar.py" "$base" | tee -a "$log" || true
echo '```' | tee -a "$log"

echo "Creando un vuelo y cambiando el estado solo por v3" | tee -a "$log"
creado="$(curl -fsS -H 'content-type: application/json' -H 'x-canary: false' \
  -d '{"numero_vuelo":"AV910","origen":"BOG","destino":"MDE","fecha":"2026-10-30","aeronave":"A320","capacidad":120}' \
  "$base/api/vuelos")"
echo "$creado" | tee -a "$log"
id="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["id"])' "$creado")"
echo '```' | tee -a "$log"
curl -fsS -H 'content-type: application/json' -H 'x-canary: true' \
  -X PUT -d '{"estado_operativo":"demorado"}' \
  "$base/api/v3/entidades/vuelos/${id}/estado" | tee -a "$log"
echo
echo "v2 sigue sin el campo:"
curl -fsS -H 'x-canary: false' "$base/api/v2/entidades/vuelos" | tee -a "$log"
echo
echo '```' | tee -a "$log"

for peso in 10 50 100; do
  echo "Pasando a ${peso}%" | tee -a "$log"
  bash "$root/canary/peso.sh" "$peso" | tee -a "$log"
  sleep 8
  echo '```' | tee -a "$log"
  contar 40 | tee -a "$log"
  echo '```' | tee -a "$log"
done

echo "Inyectando 100% de errores solo en el canary" | tee -a "$log"
curl -fsS -H 'content-type: application/json' -H 'x-canary: true' \
  -X PUT -d '{"modo":"errores","porcentaje":100}' \
  "$base/api/v3/demo/degradacion" | tee -a "$log"
echo | tee -a "$log"
bash "$root/canary/carga.sh" "$base" 40 | tee -a "$log"
echo '```' | tee -a "$log"
set +e
python3 "$root/canary/evaluar.py" "$base" | tee -a "$log"
codigo=$?
set -e
echo "exit=$codigo" | tee -a "$log"
echo '```' | tee -a "$log"

echo "Abortando a 0%" | tee -a "$log"
bash "$root/canary/peso.sh" 0 | tee -a "$log"
sleep 8
echo '```' | tee -a "$log"
contar 20 | tee -a "$log"
echo -n "stable sigue sano: "; curl -s -o /dev/null -w '%{http_code}\n' -H 'x-canary: false' "$base/api/v2/entidades/vuelos" | tee -a "$log"
echo -n "canary sigue fallando por cabecera: "; curl -s -o /dev/null -w '%{http_code}\n' -H 'x-canary: true' "$base/api/v2/entidades/vuelos" | tee -a "$log"
echo '```' | tee -a "$log"

curl -fsS -H 'content-type: application/json' -H 'x-canary: true' \
  -X PUT -d '{"modo":"off","porcentaje":0}' \
  "$base/api/v3/demo/degradacion" >/dev/null
echo "Falla apagada. Evidencia en $log"
