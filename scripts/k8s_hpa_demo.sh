#!/usr/bin/env bash
# Genera carga CPU breve para demostrar HPA (requiere kubectl + metrics-server).
set -euo pipefail
NAMESPACE="${NAMESPACE:-clic-kiusys}"
DURATION="${DURATION:-90}"

echo "Réplicas antes:"
kubectl -n "$NAMESPACE" get hpa,deploy/clic-kiusys-api

kubectl -n "$NAMESPACE" run load-hpa-$RANDOM --rm -i --restart=Never \
  --image=busybox:1.36 \
  -- sh -c "for i in \$(seq 1 $DURATION); do wget -q -O- http://clic-kiusys-api/api/v2/health >/dev/null; done" &
LOAD_PID=$!

for _ in $(seq 1 12); do
  sleep 5
  kubectl -n "$NAMESPACE" get hpa,deploy/clic-kiusys-api 2>/dev/null || true
done

wait "$LOAD_PID" 2>/dev/null || true
echo "Fin demo HPA (espera 1-2 min para scale-down)."
