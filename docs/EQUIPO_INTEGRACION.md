# Datos para compartir con el equipo (Seguimiento #2)

Copia esta plantilla al chat del grupo y rellena cuando cada uno tenga URL.

## Integrante A — Juan (OCI / OKE)

| Campo | Valor |
|-------|--------|
| Repo | https://github.com/juangz1912/clic_kiusys |
| Nube | Oracle OCI |
| URL base API | `http://___________` (LoadBalancer OKE) |
| Health v2 | `GET /api/v2/health` |
| Flujo agregado | `POST /api/v2/flujo` |
| Entidades propias | Vuelo, Pasajero, AsientoAsignado (v1) |
| Header trace | `X-Trace-Id` (obligatorio propagar) |

**Lo que necesito de ustedes:**

- `API_B_BASE_URL` + path GET lista (ej. `/api/mascotas`)
- `API_C_BASE_URL` + path GET lista (ej. `/api/items`)

## Integrante B — Alejandro Hernandez (GCP)

| Campo | Valor |
|-------|--------|
| URL base | |
| Entidad que expone | (ej. Mascota) |
| Endpoint GET lista | |

## Integrante C — Alejandro Marin (Azure/AWS)

| Campo | Valor |
|-------|--------|
| URL base | |
| Entidad que expone | (ej. Ítem) |
| Endpoint GET lista | |

## Componentes transversales (acordar quién hace qué)

| Rol | Responsable | Nube | URL |
|-----|-------------|------|-----|
| MS orquestador | | | |
| Cola / DLQ | | | |
| Caché | | | |
| Object storage | | | |

## Prueba conjunta ( día sustentación)

1. Orquestador dispara flujo en las 3 APIs.  
2. Cambiar un dato en API B o C → repetir flujo → debe verse en respuesta.  
3. Mostrar trace-id en logs de las 3 nubes.  
4. HPA + alerta grupal (si aplica).
