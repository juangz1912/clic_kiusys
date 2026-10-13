# Clic KiuSys PSS API

API REST para un mini PSS de aerolínea con las entidades **Vuelo**, **Pasajero** y **AsientoAsignado**.

Repositorio: https://github.com/juangz1912/clic_kiusys

## Arquitectura del grupo

```mermaid
flowchart LR
  Cliente[Cliente / Postman] -->|"POST /api/v2/flujo + X-Trace-Id"| Orq

  subgraph GCP["GCP - Leonardo Guevara"]
    Orq[Orquestador<br/>Cloud Run]
    PubSub[(Pub/Sub<br/>reintentos)]
    ApiC[API C documentos<br/>GKE]
  end

  subgraph AWS["AWS - Angel Avirama"]
    ApiB[API B adopción<br/>EKS]
    Redis[(ElastiCache Redis<br/>caché con TTL)]
  end

  subgraph OCI["OCI - Juan José Giraldo"]
    LB[Load Balancer<br/>157-137-193-66.sslip.io]
    ApiA[API A PSS<br/>OKE 2-5 réplicas, HPA]
    PG[(Postgres<br/>Block Volume)]
    Bucket[(Object Storage<br/>clic-kiusys-flow)]
    Consumer[Consumidor del bucket<br/>OKE]
  end

  Grafana[Grafana Cloud<br/>métricas, logs, trazas, alerta]

  Orq <-->|mensaje| PubSub
  Orq -->|"1. GET imagen"| ApiC
  Orq -->|"2. GET animal"| ApiB
  Orq -->|"3. GET vuelo, 4. POST /api/v2/mensaje"| LB --> ApiA
  ApiA --> PG
  ApiA -->|"flujo/trace_id.json"| Bucket
  Bucket --> Consumer -->|"adjuntos/trace_id/resumen.md"| Bucket
  ApiA -.->|entidades en tiempo real| ApiB
  ApiA -.-> ApiC
  ApiB --> Redis
  ApiB -.-> ApiA
  ApiB -.-> ApiC
  ApiC -.-> ApiA
  ApiC -.-> ApiB
  ApiA -. OTLP .-> Grafana
  ApiB -. OTLP .-> Grafana
  ApiC -. OTLP .-> Grafana
  Orq -. OTLP .-> Grafana
```

| Integrante | Nube | API | Componente transversal |
|------------|------|-----|------------------------|
| Juan José Giraldo | **Oracle OCI** (OKE) | API A: Vuelo, Pasajero, AsientoAsignado (este repo) | Object Storage + consumidor ([storage_consumer](storage_consumer/README.md)) y capa SaaS de observabilidad (Grafana Cloud) |
| Angel Avirama | **AWS** (EKS) | API B: Animal, Adoptante, Adopción ([Api_Pet_Adoption](https://github.com/AngelAvirama/Api_Pet_Adoption)) | Caché Redis (ElastiCache) |
| Leonardo Guevara | **GCP** (GKE + Cloud Run) | API C: Imagen, NotaMedica, DocumentoGenerado ([MedicalDevops](https://github.com/LeonardoG2005/MedicalDevops)) | Orquestador + cola Pub/Sub |

URL pública de la API A: http://157-137-193-66.sslip.io

### Servicios adicionales (OCI)

| Servicio | Para qué |
|----------|----------|
| Load Balancer flexible de OCI (Service `LoadBalancer`) | Punto de entrada único para los compañeros y el orquestador; reparte entre las réplicas y saca de rotación los pods que fallan la readiness probe. |
| DNS con `sslip.io` | Nombre estable para la IP del balanceador sin comprar dominio; es el que tienen configurado Angel, Leonardo y el orquestador. |
| OCI Container Registry (OCIR) | Registro privado en la misma región del cluster. Cada imagen lleva el SHA del commit, así un rollback apunta a una versión exacta. |
| Gestión de secretos | Kubernetes Secrets para la base, las llaves S3 del bucket y el header OTLP de Grafana; GitHub Actions Secrets para las credenciales del pipeline. Nada de eso está en git. |
| HPA + metrics-server | Escala la API de 2 a 5 réplicas por CPU (`scripts/k8s_hpa_demo.sh`). |
| OCI Monitoring, Notifications y Logging | Alarma de CPU de los nodos con aviso por correo y log group `clic-kiusys` con los logs JSON de los pods. |
| Block Volume | Disco persistente para Postgres dentro del cluster. |

- **Contrato del grupo:** cada API expone un GET random por entidad y un GET por id que trae una entidad random de cada compañero. Aquí es `GET /api/v2/entidades/vuelos/{id}` (Vuelo + Animal de Angel + Imagen de Leonardo).
- **Trace-id:** header `X-Trace-Id` y `traceparent` (W3C) en toda la cadena
- Guía detallada: [docs/GUIA_SEGUIMIENTO_2.md](docs/GUIA_SEGUIMIENTO_2.md)
- Integración del equipo: [docs/EQUIPO_INTEGRACION.md](docs/EQUIPO_INTEGRACION.md)
- Observabilidad: [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md)

## Links de sustentación

**API A en OKE** (`http://157-137-193-66.sslip.io`)

| Qué mostrar | Link |
|-------------|------|
| Swagger | http://157-137-193-66.sslip.io/docs |
| Health (nube, cluster, trace_id) | http://157-137-193-66.sslip.io/api/v2/health |
| Vuelo random | http://157-137-193-66.sslip.io/api/v2/entidades/vuelos/random |
| Pasajero random | http://157-137-193-66.sslip.io/api/v2/entidades/pasajeros/random |
| Asiento asignado random | http://157-137-193-66.sslip.io/api/v2/entidades/asientos-asignados/random |
| Vuelo por id + Animal (AWS) + Imagen (GCP) | http://157-137-193-66.sslip.io/api/v2/entidades/vuelos/1 |
| Métricas RED del pod (p50/p95) | http://157-137-193-66.sslip.io/api/v2/metrics |
| Snapshots en Object Storage | http://157-137-193-66.sslip.io/api/v2/storage/flujo |
| Mensaje de un flujo del orquestador | http://157-137-193-66.sslip.io/api/v2/storage/flujo/revision-final-1 |
| Adjunto generado por el consumidor | http://157-137-193-66.sslip.io/api/v2/storage/adjunto/revision-final-1/resumen.md |
| Estado del fallo del paso api_a | http://157-137-193-66.sslip.io/api/v2/demo/fallo-flujo |

**Observabilidad**

| Qué mostrar | Link |
|-------------|------|
| Tablero RED del grupo (Grafana Cloud) | https://browngecko19.grafana.net/d/clic-s2-red/multicloud-s2-red-por-api |
| Tablero público (sin cuenta, solo lectura) | https://browngecko19.grafana.net/public-dashboards/36289f533814429484c024d748923642 |
| Alerta "API A - errores 5xx" | https://browngecko19.grafana.net/alerting/list |
| Trazas y métricas (Explore) | https://browngecko19.grafana.net/explore |
| Alarma nativa OCI (CPU de nodos OKE) | https://cloud.oracle.com/monitoring/alarms?region=sa-bogota-1 |
| OCI Logging (log group `clic-kiusys`) | https://cloud.oracle.com/logging/log-groups?region=sa-bogota-1 |
| Cluster OKE | https://cloud.oracle.com/containers/clusters?region=sa-bogota-1 |
| Bucket `clic-kiusys-flow` | https://cloud.oracle.com/object-storage/buckets/ax5bqkfrllcm/clic-kiusys-flow/objects?region=sa-bogota-1 |

**Repositorio**

| Qué mostrar | Link |
|-------------|------|
| Release v2.3.0 | https://github.com/juangz1912/clic_kiusys/releases/tag/v2.3.0 |
| Pipelines | https://github.com/juangz1912/clic_kiusys/actions |

**Compañeros**

| API | Link |
|-----|------|
| API B Angel (AWS): animal random | http://aa11cf2e5dd814f8cbf7485099e3b46f-618055784.us-east-1.elb.amazonaws.com/api/v2/animals/random |
| API B Angel (AWS): health | http://aa11cf2e5dd814f8cbf7485099e3b46f-618055784.us-east-1.elb.amazonaws.com/api/v2/health |
| API C Leonardo (GCP): health | http://medical-documents-api-34-123-58-136.sslip.io/health |
| API C Leonardo (GCP): documentación | http://medical-documents-api-34-123-58-136.sslip.io/documentation |
| API C Leonardo (GCP): composición | http://medical-documents-api-34-123-58-136.sslip.io/api/v2/imagenes/1/composition |

**Comandos de la demo**

```bash
# Flujo completo: orquestador (GCP) -> Pub/Sub -> API C (GCP) -> API B (AWS) -> API A (OCI) -> Object Storage
curl -X POST -H "Content-Type: application/json" -H "X-Trace-Id: sustentacion-1" \
  -d '{"resource":"imagen","id":1}' https://medical-orchestrator-400345348270.us-central1.run.app/api/v2/flujo
curl http://157-137-193-66.sslip.io/api/v2/storage/flujo/sustentacion-1
curl http://157-137-193-66.sslip.io/api/v2/storage/adjunto/sustentacion-1/resumen.md

# Modificar un dato en tiempo real y verlo en el siguiente mensaje
curl -X PUT -H "Content-Type: application/json" -d '{"destino":"CTG"}' http://157-137-193-66.sslip.io/api/vuelos/1

# Escalamiento: el HPA sube de 2 a 5 réplicas (y puede disparar la alarma de CPU de OCI)
./scripts/k8s_hpa_demo.sh

# Alerta por un fallo en un paso del flujo: el paso api_a responde 500, Pub/Sub reintenta,
# la alerta pasa a Firing y llega el correo. Al desactivar, se reprocesan los mensajes y la alerta se resuelve.
./scripts/demo_fallo_flujo.sh activar
./scripts/demo_fallo_flujo.sh desactivar
```

## Entidades (v1)

| Entidad | Descripción |
|---------|-------------|
| Vuelo | Inventario / schedule del vuelo |
| Pasajero | Perfil del pasajero |
| AsientoAsignado | Asignación de asiento con hold de 10 min |

Estados de asiento: `seleccionado`, `asignado`, `expirado`.

## Endpoints principales

- CRUD v1: `/api/vuelos`, `/api/pasajeros`, `/api/asientos-asignados`
- **QUERY:** `POST /api/vuelos/query`, etc.
- Health v1: `/api/health`
- **v2 multicloud:**
  - `GET /api/v2/entidades/{vuelos|pasajeros|asientos-asignados}/random`
  - `GET /api/v2/entidades/vuelos/{id}` con una entidad random de cada compañero
  - `POST /api/v2/flujo` y `POST /api/v2/mensaje` (el mensaje queda en Object Storage)
  - `GET /api/v2/storage/flujo`, `/api/v2/storage/flujo/{trace_id}`, `/api/v2/storage/adjunto/{trace_id}/{archivo}`
  - `/api/v2/health`, `/api/v2/metrics`
  - `GET|PUT /api/v2/demo/fallo-flujo` y `GET /api/v2/demo/fallo` (solo con `DEMO_FAILURE_ENABLED=true`)
- Docs: `/docs`

## Ambientes

| Ambiente | URL cloud | API local | Base de datos |
|----------|-----------|-----------|---------------|
| **OKE (OCI, sa-bogota-1) — Seguimiento #2** | http://157-137-193-66.sslip.io | — | Postgres en cluster (block volume OCI) |
| Pruebas (Render, legado S1) | https://clic-kiusys-pruebas.onrender.com | http://localhost:8001 | postgres puerto 5433 |
| Producción (Render, legado S1) | https://clic-kiusys-prod.onrender.com | http://localhost:8002 | postgres puerto 5434 |

## Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest --cov=app --cov-report=term-missing
docker compose up -d
python scripts/test_v2_endpoints.py http://localhost:8001
```

Variables Seguimiento #2: ver [.env.example](.env.example).

## Despliegue Render (Seguimiento #1)

El archivo `render.yaml` define 2 Web Services y **1 instancia PostgreSQL** con 2 bases (`pss_pruebas`, `pss_produccion`).

Secrets GitHub: `RENDER_DEPLOY_HOOK_PRUEBAS`, `RENDER_DEPLOY_HOOK_PRODUCCION`, `RENDER_API_KEY`.

## Terraform (Seguimiento #3)

La infraestructura de OCI se crea con Terraform, un archivo por servicio, en [terraform/readme.md](terraform/readme.md).

```bash
cd terraform
source ./env.sh
terraform apply
bash instalar_api.sh
bash destruir.sh    # al terminar la sustentación
```

API de esta ejecución: http://157.137.198.114/api/v2/health

## Despliegue OKE (Seguimiento #2)

Guía completa: [docs/OCI_DEPLOY.md](docs/OCI_DEPLOY.md)

```bash
cp scripts/oci/oci.env.example scripts/oci/oci.env   # completar y NO commitear
chmod +x scripts/oci/*.sh
./scripts/oci/deploy_all.sh
```

Plantilla para el equipo: [docs/EQUIPO_INTEGRACION.md](docs/EQUIPO_INTEGRACION.md)

## Pipelines

- `terraform-oci.yml` — manual: `terraform apply` e instala el API en la VM
- `terraform-destruir.yml` — manual: `terraform destroy`
- `deploy-oke.yml` — manual. El clúster del seguimiento 2 ya no existe
- `deploy-storage-consumer.yml` — en `main` cuando cambia `storage_consumer/`: tests, imagen a OCIR y rollout del consumidor
- `deploy-render.yml` — hook de Render en `develop` (pruebas) y `main` (producción)

## Stack

- Python 3.12 + FastAPI
- PostgreSQL
- Docker / OKE (Kubernetes)
- Render + **Oracle OCI**
- GitHub Actions

## Versionado

Ver [CHANGELOG.md](CHANGELOG.md). Release **v3.0.0** (Seguimiento #3: infraestructura OCI con Terraform).
