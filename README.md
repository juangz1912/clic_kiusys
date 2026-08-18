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

| Ambiente | API local | Base de datos |
|----------|-----------|---------------|
| Pruebas | http://localhost:8001 | postgres puerto 5433 |
| Producción | http://localhost:8002 | postgres puerto 5434 |

## Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest --cov=app --cov-report=term-missing
docker compose up -d
```

## Pipelines

- `.github/workflows/ci-pruebas.yml` → rama `develop`, cobertura mínima **60%**
- `.github/workflows/ci-produccion.yml` → rama `main`, cobertura mínima **85%**

Si falla un test o la cobertura, el pipeline se detiene y no despliega.

## Stack

- Python 3.12 + FastAPI
- PostgreSQL
- Docker / Docker Compose
- GitHub Actions
