#!/usr/bin/env bash
# Carga concurrente contra la API en el cluster para que el HPA suba de 2 réplicas.
set -euo pipefail
NAMESPACE="${NAMESPACE:-clic-kiusys}"
WORKERS="${WORKERS:-6}"
SECONDS_LOAD="${SECONDS_LOAD:-90}"

echo "Réplicas antes:"
kubectl -n "$NAMESPACE" get hpa
kubectl -n "$NAMESPACE" get deploy clic-kiusys-api

for i in $(seq 1 "$WORKERS"); do
  kubectl -n "$NAMESPACE" run "load-hpa-$i" --restart=Never --image=docker.io/library/busybox:1.36 \
    --command -- sh -c "end=\$((\$(date +%s)+$SECONDS_LOAD)); while [ \$(date +%s) -lt \$end ]; do wget -q -O /dev/null http://clic-kiusys-api/api/v2/health || true; done" &
done

for _ in $(seq 1 18); do
  sleep 5
  kubectl -n "$NAMESPACE" get hpa clic-kiusys-api
done

wait || true
kubectl -n "$NAMESPACE" delete pod -l run --wait=false 2>/dev/null || true
for i in $(seq 1 "$WORKERS"); do
  kubectl -n "$NAMESPACE" delete pod "load-hpa-$i" --wait=false 2>/dev/null || true
done
echo "Fin de la carga. El scale-down tarda 1-5 min."
