# Guion de sustentacion — Seguimiento #1

**Estudiante:** Juan Jose Giraldo  
**Fecha:** 19 de agosto de 2026  
**Duracion sugerida:** 5–7 minutos  

---

## Links para entregar al profesor

| Recurso | URL |
|---------|-----|
| Repositorio | https://github.com/juangz1912/clic_kiusys |
| Ambiente pruebas | https://clic-kiusys-pruebas.onrender.com/docs |
| Ambiente produccion | https://clic-kiusys-prod.onrender.com/docs |
| GitHub Actions | https://github.com/juangz1912/clic_kiusys/actions |

---

## Demo en vivo (paso a paso)

### 1. Mostrar arquitectura (30 s)

- Dos ambientes independientes: **pruebas** (`develop`) y **produccion** (`main`)
- Cada uno con URL publica, PostgreSQL separada y variables de entorno distintas
- CI/CD despliega a Render solo si pasan tests y cobertura

### 2. Abrir Swagger en nube (30 s)

Abrir en el navegador:

- Pruebas: `/docs` en `clic-kiusys-pruebas.onrender.com`
- Produccion: `/docs` en `clic-kiusys-prod.onrender.com`

Mencionar: FastAPI genera la documentacion automaticamente.

### 3. CRUD Vuelo + Pasajero (1 min)

En ambiente **pruebas** (`/docs`):

1. `POST /api/vuelos` — crear vuelo AV100 BOG→MDE
2. `GET /api/vuelos/{id}` — consultar
3. `POST /api/pasajeros` — crear pasajero

### 4. Flujo AsientoAsignado con hold (2 min)

1. `POST /api/asientos-asignados` con `"estado": "seleccionado"`
2. Explicar: el asiento queda en **hold 10 minutos** (`HOLD_MINUTES=10`)
3. `PUT /api/asientos-asignados/{id}` cambiar a `"estado": "asignado"`
4. Mencionar que si no confirma, pasa a `expirado` via `expire_holds`

### 5. QUERY (1 min)

`POST /api/asientos-asignados/query`:

```json
{
  "vuelo_id": 1,
  "estado": "asignado"
}
```

Repetir con `POST /api/vuelos/query` filtrando por origen.

### 6. Pipelines CI/CD (1 min)

Mostrar GitHub Actions:

- **ci-pruebas.yml**: rama `develop`, gate **60%** cobertura
- **ci-produccion.yml**: rama `main`, gate **85%** cobertura
- Si falla test o cobertura → pipeline rojo, **no despliega**
- Tras pasar tests → Deploy Hook a Render + smoke test a URL publica

### 7. Docker (30 s)

- `Dockerfile` multi-stage slim con Python 3.12
- `docker-compose.yml` levanta 2 stacks locales (8001 pruebas / 8002 produccion)
- Misma imagen que usa Render en cloud

---

## Preguntas frecuentes del profesor

**Por que 3 entidades?**  
Vuelo (inventario), Pasajero (perfil), AsientoAsignado (asignacion con estado y hold).

**Como son independientes los ambientes?**  
URL distinta, BD PostgreSQL distinta en Render, secrets y variables separadas, ramas Git distintas.

**Que pasa si un test falla?**  
El pipeline se detiene; no se llama al Deploy Hook de Render.

**Por que Docker?**  
Empaqueta la app con dependencias; mismo comportamiento local, en CI y en nube.

**Que es el verbo QUERY?**  
`POST .../query` con filtros en JSON — busqueda flexible sin inventar GET con 20 parametros.

---

## Checklist antes de entrar a sustentar

- [ ] Ambas URLs cloud responden `/api/health`
- [ ] Datos demo sembrados (`./scripts/seed_demo.sh`)
- [ ] GitHub Actions en verde en `develop` y `main`
- [ ] Pestañas abiertas: docs pruebas, docs prod, Actions
- [ ] Entidades confirmadas con el docente
