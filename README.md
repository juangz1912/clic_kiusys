# Clic KiuSys PSS API

API REST para un mini PSS de aerolínea con las entidades **Vuelo**, **Pasajero** y **AsientoAsignado**.

Repositorio: https://github.com/juangz1912/clic_kiusys

## Entidades

| Entidad | Descripción |
|---------|-------------|
| Vuelo | Inventario / schedule del vuelo |
| Pasajero | Perfil del pasajero |
| AsientoAsignado | Asignación de asiento con hold de 10 min |

Estados de asiento: `seleccionado`, `asignado`, `expirado`.

## Endpoints principales

- CRUD: `/api/vuelos`, `/api/pasajeros`, `/api/asientos-asignados`
- **QUERY**: `POST /api/vuelos/query`, `POST /api/pasajeros/query`, `POST /api/asientos-asignados/query`
- Health: `/api/health`
- Docs: `/docs`

## Ambientes

| Ambiente | URL cloud | API local | Base de datos |
|----------|-----------|-----------|---------------|
| Pruebas | https://clic-kiusys-pruebas.onrender.com | http://localhost:8001 | postgres puerto 5433 |
| Producción | https://clic-kiusys-prod.onrender.com | http://localhost:8002 | postgres puerto 5434 |

Documentación interactiva:

- Pruebas: https://clic-kiusys-pruebas.onrender.com/docs
- Producción: https://clic-kiusys-prod.onrender.com/docs

## Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest --cov=app --cov-report=term-missing
docker compose up -d
```

Sembrar datos demo:

```bash
./scripts/seed_demo.sh
BASE_URL=https://clic-kiusys-pruebas.onrender.com ./scripts/seed_demo.sh
```

## Despliegue en Render

El archivo `render.yaml` define 2 Web Services (pruebas/producción) y **1 instancia PostgreSQL** con 2 bases de datos separadas (`pss_pruebas`, `pss_produccion`) en el plan free tier.

1. Render Dashboard → **Blueprints** → **New Blueprint Instance**
2. Conectar repo `juangz1912/clic_kiusys`
3. Aplicar blueprint (crea BD y servicios automáticamente)
4. En cada Web Service → **Settings** → **Deploy Hook** → copiar URL
5. GitHub → Settings → Secrets → Actions:
   - `RENDER_DEPLOY_HOOK_PRUEBAS`
   - `RENDER_DEPLOY_HOOK_PRODUCCION`
   - `RENDER_API_KEY` (fallback si no hay Deploy Hook; usado por el pipeline para disparar deploy)

## Pipelines

- `.github/workflows/ci-pruebas.yml` → rama `develop`, cobertura mínima **60%**, deploy a Render pruebas
- `.github/workflows/ci-produccion.yml` → rama `main`, cobertura mínima **85%**, deploy a Render producción

Flujo: tests → build Docker → smoke local → deploy Render → smoke cloud con `scripts/test_all_endpoints.py` (25 endpoints).

Si falla un test o la cobertura, el pipeline se detiene y no despliega.

GitHub Actions: https://github.com/juangz1912/clic_kiusys/actions

## Stack

- Python 3.12 + FastAPI
- PostgreSQL
- Docker / Docker Compose
- Render (cloud)
- GitHub Actions

