# Despliegue Oracle OCI (OKE) — clic_kiusys

Guía paso a paso **sin MCP**: solo consola OCI, OCI CLI, Docker y `kubectl`.

## 0. Prerrequisitos en tu Mac

```bash
# OCI CLI (si no lo tienes)
brew install oci-cli
oci setup config

# kubectl
brew install kubectl

# Docker Desktop o engine corriendo
docker info
```

## 1. Crear recursos en consola OCI (una vez)

| Recurso | Sugerencia |
|---------|------------|
| **Compartment** | `clic-kiusys-dev` |
| **VCN + subnets** | Asistente “VCN with Internet Connectivity” |
| **OKE cluster** | Quick create, **2+ nodes**, Kubernetes 1.28+ |
| **Autonomous PostgreSQL** | O bien PostgreSQL en compute; guardar **connection string** |
| **OCIR** | Repositorio `clic-kiusys` en Container Registry |

Anota:

- `OKE_CLUSTER_ID` (OCID del cluster)
- `OCI_REGION` (ej. `sa-bogota-1`)
- Namespace OCIR (tenancy namespace)
- Auth token OCIR (User Settings → Auth Tokens)

## 2. Configurar variables locales

```bash
cp scripts/oci/oci.env.example scripts/oci/oci.env
# Editar scripts/oci/oci.env (NO commitear)
```

Completa al menos: región, OCIR, token, cluster ID, `DATABASE_URL`.

## 3. Despliegue automatizado (recomendado)

```bash
chmod +x scripts/oci/*.sh
./scripts/oci/deploy_all.sh
```

Pasos que ejecuta:

1. `01_login_ocir.sh` — login Docker en OCIR  
2. `02_build_push.sh` — build + push imagen `v2.0.0`  
3. `03_kubeconfig.sh` — `kubectl` apuntando al OKE  
4. `04_create_secret.sh` — Secret BD + URLs B/C + pull secret OCIR  
5. `05_deploy_oke.sh` — Deployment (2 réplicas), Service, **LoadBalancer OCI**, HPA  
6. `06_verify.sh` — estado pods/HPA y smoke v2  

## 4. URL pública

```bash
kubectl -n clic-kiusys get svc clic-kiusys-api-lb
```

Cuando aparezca **EXTERNAL-IP** o hostname:

```bash
curl -s "http://EXTERNAL-IP/api/v2/health" | python3 -m json.tool
python3 scripts/test_v2_endpoints.py "http://EXTERNAL-IP"
```

## 5. Integración compañeros (Angel AWS / Leonardo GCP)

En `scripts/oci/oci.env` ya están las URLs públicas. Si cambian:

```bash
API_B_BASE_URL=http://aa11cf2e5dd814f8cbf7485099e3b46f-618055784.us-east-1.elb.amazonaws.com
API_C_BASE_URL=http://medical-documents-api-34-123-58-136.sslip.io
INTEGRATION_STUB_WHEN_UNREACHABLE=false
```

Vuelve a aplicar secret:

```bash
./scripts/oci/04_create_secret.sh
kubectl -n clic-kiusys rollout restart deployment/clic-kiusys-api
```

Prueba:

```bash
curl -s -X POST "http://EXTERNAL-IP/api/v2/flujo" -H "Content-Type: application/json" -d '{}' | python3 -m json.tool
```

## 6. Evidencias sustentación (capturas)

- `kubectl get pods,hpa,svc -n clic-kiusys`
- Swagger o Postman: `POST /api/v2/flujo` con trace-id
- OCI Console → **Logging & Monitoring** del cluster/workload
- (Grupo) dashboard SaaS con trace-id correlacionado

## 7. Escalamiento HPA (demo)

```bash
# Opcional: generar carga ligera
for i in $(seq 1 200); do curl -sf "http://EXTERNAL-IP/api/v2/health" >/dev/null & done
kubectl -n clic-kiusys get hpa -w
```

## 8. Problemas frecuentes

| Síntoma | Qué revisar |
|---------|-------------|
| `ImagePullBackOff` | `ocir-secret`, nombre imagen en deployment, login OCIR |
| Pods `CrashLoopBackOff` | `DATABASE_URL`, logs `kubectl logs -n clic-kiusys deploy/clic-kiusys-api` |
| LB sin IP | Esperar 2–5 min; políticas de subnet / security lists |
| Flujo v2 sin B/C | URLs en secret; CORS/firewall entre nubes |

## 9. Manifiestos alternativos

- `k8s/ingress.yaml` — si instalas NGINX Ingress Controller (opcional).
- Por defecto usamos **`k8s/service-lb.yaml`** (Load Balancer nativo OCI).
