#!/usr/bin/env bash
# Alarma nativa de OCI Monitoring: CPU de los nodos de OKE > 80 %, avisa por correo (OCI Notifications).
# La carga de scripts/k8s_hpa_demo.sh la puede disparar. Hay que confirmar el correo que manda OCI.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

C="$OCI_COMPARTMENT_ID"
EMAIL="${ALARM_EMAIL:-jujosal007@gmail.com}"
TOPIC_NAME="clic-kiusys-alertas"
ALARM_NAME="clic-kiusys-oke-cpu-alta"

TOPIC_ID=$(oci ons topic list -c "$C" --all --query "data[?name=='$TOPIC_NAME'].\"topic-id\" | [0]" --raw-output 2>/dev/null || true)
if [[ "$TOPIC_ID" != ocid* ]]; then
  TOPIC_ID=$(oci ons topic create -c "$C" --name "$TOPIC_NAME" \
    --description "Alertas API A Seguimiento 2" --query 'data."topic-id"' --raw-output)
  echo "Topic creado: $TOPIC_NAME"
else
  echo "Topic ya existe: $TOPIC_NAME"
fi

if oci ons subscription list -c "$C" --topic-id "$TOPIC_ID" --all \
  --query "data[?endpoint=='$EMAIL'].id | [0]" --raw-output 2>/dev/null | grep -q ocid; then
  echo "Suscripción de $EMAIL ya existe"
else
  oci ons subscription create -c "$C" --topic-id "$TOPIC_ID" --protocol EMAIL --subscription-endpoint "$EMAIL" >/dev/null
  echo "Suscripción creada: confirma el correo de OCI en $EMAIL"
fi

QUERY='CpuUtilization[1m]{resourceDisplayName =~ "oke-*"}.mean() > 80'
ALARM_ID=$(oci monitoring alarm list -c "$C" --all --query "data[?\"display-name\"=='$ALARM_NAME'].id | [0]" --raw-output 2>/dev/null || true)
if [[ "$ALARM_ID" == ocid* ]]; then
  oci monitoring alarm update --alarm-id "$ALARM_ID" --query-text "$QUERY" --force >/dev/null
  echo "Alarma actualizada: $ALARM_NAME"
else
  oci monitoring alarm create -c "$C" --display-name "$ALARM_NAME" \
    --metric-compartment-id "$C" --namespace oci_computeagent \
    --query-text "$QUERY" --severity CRITICAL --pending-duration PT1M \
    --body "CPU de un nodo de OKE (clic-kiusys-oke) por encima de 80 %. El HPA debería estar escalando la API." \
    --destinations "[\"$TOPIC_ID\"]" --is-enabled true >/dev/null
  echo "Alarma creada: $ALARM_NAME"
fi
echo "Consola: https://cloud.oracle.com/monitoring/alarms?region=${OCI_REGION}"
