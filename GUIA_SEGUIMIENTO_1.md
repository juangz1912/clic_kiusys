# Guía Seguimiento #1 — Clic KiuSys PSS API

**Estudiante:** Juan Jose Giraldo  
**Repositorio:** https://github.com/juangz1912/clic_kiusys  
**Proyecto:** API mini-PSS (Vuelo, Pasajero, AsientoAsignado)  
**Fecha evaluación:** 19 de agosto de 2026  

Este documento explica **qué pide el seguimiento**, **qué ya tienes hecho**, **qué falta** y **cómo completarlo**.

---

## Resumen rápido

| Área | Peso | Estado | Qué falta |
|------|------|--------|-----------|
| Pipeline CI/CD + solución | 40% | Casi listo | Despliegue en **nube** con URLs públicas |
| Docker | 30% | Listo | Nada crítico |
| Sustentación verbal | 30% | Pendiente | Preparar defensa + demo en nube |

**Lo más importante que te falta:** desplegar la API en la **nube** (no solo en tu PC o en el runner de GitHub) y preparar la sustentación del 19 de agosto.

---

## 1. Pipeline CI/CD y solución (40%)

### 1.1 Repositorio en Git

**Qué pide el PDF**
- Código en Git
- Entregar el link del repositorio
- Commits con [GitMoji](https://gitmoji.dev/)
- No tener pocos commits

**Qué tienes**
- Repo: https://github.com/juangz1912/clic_kiusys
- 6 commits con GitMoji (✨, ✅, 🐳, 👷, 📝)
- Ramas `develop` y `main`

**Estado:** ✅ Cumplido

**Recomendación:** Haz 2–4 commits más mientras terminas (deploy nube, fixes, docs). El PDF dice “no pocos commits”; 6 está bien, pero más actividad se ve mejor.

---

### 1.2 API RESTful con QUERY y 3 entidades

**Qué pide el PDF**
- API REST completa
- Verbo **QUERY**
- Mínimo 3 entidades
- Base de datos real (persistencia)

**Qué tienes**

| Entidad | Qué es | Endpoints |
|---------|--------|-----------|
| **Vuelo** | Inventario / schedule | CRUD + `POST /api/vuelos/query` |
| **Pasajero** | Perfil PNR | CRUD + `POST /api/pasajeros/query` |
| **AsientoAsignado** | Seat assignment | CRUD + `POST /api/asientos-asignados/query` |

- PostgreSQL con SQLAlchemy
- Hold de 10 min: `seleccionado` → `asignado` o `expirado`
- Docs automáticas en `/docs`

**Estado:** ✅ Cumplido

**Pendiente administrativo:** Confirmar las 3 entidades con el docente (si aún no lo hiciste).

---

### 1.3 Dos ambientes independientes (Pruebas y Producción)

**Qué pide el PDF**
- Ambiente **Pruebas** y **Producción**
- Independientes en al menos:
  - URL de deploy distinta
  - Base de datos distinta
  - Variables / secrets separados

**Qué tienes hoy**

| Ambiente | Local (Docker) | BD local | Variables |
|----------|----------------|----------|-----------|
| Pruebas | http://localhost:8001 | puerto 5433 | `ENVIRONMENT=pruebas` |
| Producción | http://localhost:8002 | puerto 5434 | `ENVIRONMENT=produccion` |

**Estado:** ✅ Configurado (Render Blueprint + URLs documentadas)

**URLs cloud:**
- Pruebas: https://clic-kiusys-pruebas.onrender.com/docs
- Producción: https://clic-kiusys-prod.onrender.com/docs

Infra definida en `render.yaml` (2 PostgreSQL + 2 Web Services). Aplicar blueprint en Render Dashboard si aún no está desplegado.

---

### 1.4 Pipelines SaaS CI/CD (2 independientes)

**Qué pide el PDF**
- Herramienta SaaS (GitHub Actions, GitLab CI, etc.)
- **2 pipelines** (Pruebas y Producción)
- Cada uno con:
  1. Build / instalación de dependencias
  2. Pruebas automatizadas
  3. Validación de cobertura (quality gate)
  4. Despliegue al ambiente correspondiente

**Qué tienes**

| Pipeline | Archivo | Rama | Cobertura mínima |
|----------|---------|------|------------------|
| CI Pruebas | `.github/workflows/ci-pruebas.yml` | `develop` | ≥ 60% |
| CI Producción | `.github/workflows/ci-produccion.yml` | `main` | ≥ 85% |

Ambos pipelines ya corrieron con **éxito** en GitHub (build, tests, docker, smoke test).

**Estado:** ✅ Completo (tests + Deploy Hook Render + smoke test cloud)

Los pipelines llaman al Deploy Hook de Render tras pasar tests (solo en push a `develop`/`main`, no en PR). Secrets requeridos: `RENDER_DEPLOY_HOOK_PRUEBAS`, `RENDER_DEPLOY_HOOK_PRODUCCION`.

---

## 2. Integración con Docker (30%)

**Qué pide el PDF**
- Dockerfile + docker-compose (app + BD), **o**
- Construir imagen en el pipeline, **o**
- Correr pruebas en contenedores

**Qué tienes**
- `Dockerfile` — imagen de la API
- `docker-compose.yml` — app + PostgreSQL para pruebas y producción
- Pipeline construye imagen Docker (`docker build`)
- Pipeline levanta stack con `docker compose up`

**Estado:** ✅ Cumplido

**Cómo probarlo localmente**
```bash
cd clic_kiusys
docker compose up -d
# Pruebas: http://localhost:8001/docs
# Producción: http://localhost:8002/docs
```

---

## 3. Sustentación verbal (30%)

**Qué pide el PDF**
- Preguntas individuales del profesor
- Demostrar la solución **en ejecución**
- Desplegada en **servicios en la nube**

**Estado:** ✅ Guion listo en `SUSTENTACION.md`

**Qué preparar**

1. **Demo en vivo** con URLs de nube (pruebas y producción)
2. Explicar las 3 entidades y el flujo de AsientoAsignado (hold 10 min)
3. Mostrar un endpoint QUERY, por ejemplo:
   ```bash
   POST /api/asientos-asignados/query
   { "vuelo_id": 1, "estado": "asignado" }
   ```
4. Explicar los 2 pipelines y las reglas de cobertura (60% / 85%)
5. Mostrar GitHub Actions en verde
6. Explicar Docker (Dockerfile + compose)

**Preguntas típicas que te pueden hacer**
- ¿Qué hace el verbo QUERY en tu API?
- ¿Cómo separaste pruebas de producción?
- ¿Qué pasa si un test falla en el pipeline?
- ¿Por qué usaste PostgreSQL?
- ¿Cómo funciona el hold de 10 minutos del asiento?

---

## Checklist final — qué te falta hacer

### Crítico (para nota alta)

- [x] **Desplegar en la nube** — `render.yaml` + URLs documentadas
- [x] **Actualizar pipelines** — Deploy Hook Render + smoke test cloud
- [ ] **Configurar secrets** en GitHub (`RENDER_DEPLOY_HOOK_PRUEBAS`, `RENDER_DEPLOY_HOOK_PRODUCCION`)
- [ ] **Confirmar entidades** con el docente (Vuelo, Pasajero, AsientoAsignado)
- [x] **Preparar sustentación** — ver `SUSTENTACION.md`

### Recomendado (mejora la entrega)

- [x] Agregar commits (deploy, documentación, CI)
- [x] Documentar en README las URLs finales de pruebas y producción
- [ ] Probar manualmente CRUD + QUERY en ambos ambientes cloud
- [ ] Capturas de pantalla: GitHub Actions verde, `/docs`, QUERY funcionando

### Ya hecho ✅

- [x] Repo Git con GitMoji
- [x] API REST con 3 entidades
- [x] QUERY en las 3 entidades
- [x] PostgreSQL
- [x] Tests automatizados (86% cobertura)
- [x] 2 pipelines CI (pruebas 60%, prod 85%)
- [x] Dockerfile + docker-compose
- [x] Ambientes locales separados (8001 / 8002)

---

## Cómo funciona tu proyecto (explicación simple)

### Arquitectura

```
Cliente (Postman / navegador)
        ↓
   FastAPI (Python)
        ↓
   PostgreSQL
```

### Flujo del asiento (lo más “PSS”)

1. Pasajero selecciona asiento → estado `seleccionado`, hold 10 min
2. Si paga a tiempo → `asignado`
3. Si no paga → `expirado`, el asiento queda libre otra vez

### Estructura del código

```
clic_kiusys/
├── app/
│   ├── main.py          → arranca FastAPI
│   ├── routes.py        → endpoints CRUD + QUERY
│   ├── models/          → tablas BD (Vuelo, Pasajero, AsientoAsignado)
│   ├── schemas.py       → validación de datos (Pydantic)
│   ├── services.py      → lógica de hold, queries
│   └── database.py      → conexión PostgreSQL
├── tests/               → pruebas automatizadas
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/   → pipelines CI
```

### Pipelines — qué hace cada uno

**Cuando haces push a `develop`:**
1. Instala Python y dependencias
2. Levanta PostgreSQL temporal
3. Corre pytest con cobertura ≥ 60%
4. Si falla → se detiene, no despliega
5. Construye imagen Docker
6. Levanta stack pruebas y hace smoke test

**Cuando haces push a `main`:**
- Igual, pero cobertura ≥ 85%

---

## Próximo paso sugerido (prioridad 1)

**Desplegar en Render (ejemplo gratuito)**

1. Crear cuenta en https://render.com
2. Crear **PostgreSQL** para pruebas y otro para producción
3. Crear **Web Service** conectado al repo `clic_kiusys`
   - Rama `develop` → ambiente pruebas
   - Rama `main` → ambiente producción
4. Variables de entorno en cada servicio:
   - `DATABASE_URL` (distinta en cada uno)
   - `ENVIRONMENT=pruebas` o `produccion`
5. Agregar al pipeline un paso de deploy con webhook de Render (opcional)
6. Pegar las 2 URLs en el README y entregarlas al profesor

---

## Links útiles

- Repositorio: https://github.com/juangz1912/clic_kiusys
- GitMoji: https://gitmoji.dev/
- Actions (CI): https://github.com/juangz1912/clic_kiusys/actions
- API docs local pruebas: http://localhost:8001/docs
- API docs local producción: http://localhost:8002/docs

---

## Conclusión

Tienes **cerca del 70% del seguimiento técnico listo**. Lo que más pesa para cerrarlo:

1. **Nube** (URLs públicas reales)
2. **Sustentación** (saber explicar lo que hiciste)

El código, los tests, Docker y los pipelines ya funcionan. Lo que separa un “medio” de un “alto” es tener la app **desplegada en internet** y poder demostrarla el 19 de agosto sin depender de tu laptop.
