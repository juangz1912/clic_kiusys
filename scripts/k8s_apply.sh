#!/usr/bin/env bash
# Aplica manifiestos OKE/Kubernetes (requiere kubectl configurado).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
kubectl apply -f "$ROOT/k8s/namespace.yaml"
kubectl apply -f "$ROOT/k8s/configmap.yaml"
echo "Crea el Secret desde k8s/secret.yaml.example antes de desplegar el Deployment."
kubectl apply -f "$ROOT/k8s/deployment.yaml"
kubectl apply -f "$ROOT/k8s/service.yaml"
kubectl apply -f "$ROOT/k8s/ingress.yaml"
kubectl apply -f "$ROOT/k8s/hpa.yaml"
kubectl -n clic-kiusys get all
