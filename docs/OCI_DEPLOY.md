# Despliegue en Oracle OCI (OKE)

1. Crear cluster OKE en la región acordada con el equipo.
2. `oci ce cluster create-kubeconfig` o equivalente para `kubectl`.
3. Provisionar Autonomous Database PostgreSQL y obtener cadena de conexión.
4. Editar `k8s/secret.yaml.example` → `kubectl apply -f k8s/secret.yaml`.
5. Publicar imagen: `docker build -t clic-kiusys:v2 .` y push al registry de OCI.
6. Actualizar `k8s/deployment.yaml` con la imagen real.
7. `./scripts/k8s_apply.sh`
8. Configurar Ingress/DNS público y probar `GET /api/v2/health`.
