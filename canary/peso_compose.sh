#!/bin/bash
# Cambia el peso del canary en el nginx local. Mismos escalones que el balanceador de OCI.
set -euo pipefail
porcentaje="${1:?uso: peso_compose.sh 0|10|50|100}"
case "$porcentaje" in
  0|10|50|100) ;;
  *) echo "porcentaje inválido" >&2; exit 1 ;;
esac

dir="$(cd "$(dirname "$0")/compose" && pwd)"
plantilla="$dir/nginx.conf.template"
salida="$dir/nginx.conf"
estable=$((100 - porcentaje))

if [ "$porcentaje" -eq 0 ]; then
  linea=""
elif [ "$porcentaje" -eq 100 ]; then
  # A 100% el público solo ve el canary. Stable sigue por la cabecera.
  estable=0
  linea="    server canary:8000 weight=${porcentaje};"
else
  linea="    server canary:8000 weight=${porcentaje};"
fi

if [ "$estable" -eq 0 ]; then
  cuerpo="$(sed '/weight=STABLE_WEIGHT/d' "$plantilla")"
else
  cuerpo="$(sed "s/weight=STABLE_WEIGHT/weight=${estable}/" "$plantilla")"
fi
printf '%s\n' "$cuerpo" | sed "s|CANARY_LINE|${linea}|" > "$salida"

if docker compose -f "$dir/docker-compose.yml" ps --status running --services 2>/dev/null | grep -qx nginx; then
  docker compose -f "$dir/docker-compose.yml" exec -T nginx nginx -s reload
fi
echo "canary_percent=${porcentaje}"
