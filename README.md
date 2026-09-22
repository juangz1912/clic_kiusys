# Clic KiuSys PSS API

API REST para un mini PSS de aerolínea con las entidades **Vuelo**, **Pasajero** y **AsientoAsignado**.

Repositorio: https://github.com/juangz1912/clic_kiusys

## Seguimiento #2 — Multicloud (OCI)

| Integrante | Nube | Rol |
|------------|------|-----|
| Juan Jose Giraldo | **Oracle OCI (OKE)** | API A + Object Storage |
| Angel Avirama | **AWS** | API B — adopción ([Api_Pet_Adoption](https://github.com/AngelAvirama/Api_Pet_Adoption)) |
| Leonardo Giraldo | **GCP** | API C — documentos médicos ([MedicalDevops](https://github.com/LeonardoG2005/MedicalDevops)) |

- **API v2:** `/api/v2/health`, `POST /api/v2/flujo` (vínculos Animal–Vuelo–Imagen, Adoptante–Pasajero–NotaMedica, Adopcion–AsientoAsignado–DocumentoGenerado), `/api/v2/metrics`
- **Trace-id:** header `X-Trace-Id` en toda la cadena
- Guía detallada: [docs/GUIA_SEGUIMIENTO_2.md](docs/GUIA_SEGUIMIENTO_2.md)
- Integración del equipo: [docs/EQUIPO_INTEGRACION.md](docs/EQUIPO_INTEGRACION.md)

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
- **v2 multicloud:** `/api/v2/health`, `POST /api/v2/flujo`, `/api/v2/metrics`
- Docs: `/docs`

## Ambientes

| Ambiente | URL cloud | API local | Base de datos |
|----------|-----------|-----------|---------------|
| Pruebas (Render) | https://clic-kiusys-pruebas.onrender.com | http://localhost:8001 | postgres puerto 5433 |
| Producción (Render) | https://clic-kiusys-prod.onrender.com | http://localhost:8002 | postgres puerto 5434 |
| OKE (OCI) | Ingress configurado en `k8s/ingress.yaml` | — | Autonomous DB (equipo) |

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

## Despliegue OKE (Seguimiento #2)

Guía completa: [docs/OCI_DEPLOY.md](docs/OCI_DEPLOY.md)

```bash
cp scripts/oci/oci.env.example scripts/oci/oci.env   # completar y NO commitear
chmod +x scripts/oci/*.sh
./scripts/oci/deploy_all.sh
```

Plantilla para el equipo: [docs/EQUIPO_INTEGRACION.md](docs/EQUIPO_INTEGRACION.md)

## Pipelines

- `ci-pruebas.yml` / `ci-produccion.yml` — tests, Docker, Render
- `k8s-validate.yml` — validación de manifiestos Kubernetes

## Stack

- Python 3.12 + FastAPI
- PostgreSQL
- Docker / OKE (Kubernetes)
- Render + **Oracle OCI**
- GitHub Actions

## Versionado

Ver [CHANGELOG.md](CHANGELOG.md). Release **v2.0.0** (Seguimiento #2).
