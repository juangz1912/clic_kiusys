# Datos para compartir con el equipo (Seguimiento #2)

Generar bloque listo para el chat:

```bash
./scripts/handoff_equipo.sh http://157-137-193-66.sslip.io
```

## Integrante A — Juan (OCI / OKE + Object Storage)

| Campo | Valor |
|-------|--------|
| Repo | https://github.com/juangz1912/clic_kiusys |
| Nube | **Oracle OCI** |
| Rol transversal | **Object Storage** + consumidor (JSON flujo + adjuntos) |
| URL base API (OKE) | http://157-137-193-66.sslip.io |
| Cluster | OKE `clic-kiusys-oke`, sa-bogota-1, 2 nodos E5.Flex, HPA 2-5 réplicas |

### Endpoints v2 (header `X-Trace-Id` obligatorio)

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/api/v2/health` | Health + metadata OCI |
| POST | `/api/v2/flujo` | Tres vínculos locales + HTTP B/C; guarda JSON en Object Storage |
| GET | `/api/v2/metrics` | Métricas RED v2 |
| GET | `/api/v2/entidades/vuelos` | Consumir Vuelo desde B/C |
| GET | `/api/v2/entidades/pasajeros` | Consumir Pasajero desde B/C |
| GET | `/api/v2/entidades/asientos-asignados` | Consumir AsientoAsignado desde B/C |
| GET | `/api/v2/storage/flujo/{trace_id}` | Snapshot del flujo |
| POST | `/api/v2/storage/adjunto` | Subir adjunto (multipart + `X-Trace-Id`) |
| GET | `/api/v2/storage/adjunto/{trace_id}/{filename}` | Descargar adjunto |

## Mapeo de entidades

| API A (Juan / OCI) | API B Angel (AWS) | API C Leonardo (GCP) |
|--------------------|-------------------|----------------------|
| Vuelo | Animal `GET /api/v2/animals` | Imagen `GET /imagenes` |
| Pasajero | Adoptante `GET /api/v2/adoptantes` | NotaMedica `GET /notas-medicas` |
| AsientoAsignado | Adopcion `GET /api/v2/adopciones` | DocumentoGenerado `GET /documentos-generados` |

`POST /api/v2/flujo` responde `vinculos[]` con esos tres roles. Angel envuelve listas en `{ "data": [...] }`; Leonardo responde array JSON.

## Integrante B — Angel Avirama (AWS)

| Campo | Valor |
|-------|--------|
| Repo | https://github.com/AngelAvirama/Api_Pet_Adoption |
| URL base | `http://aa11cf2e5dd814f8cbf7485099e3b46f-618055784.us-east-1.elb.amazonaws.com` |
| Health | `GET /api/v2/health` |
| Listas v2 | `/api/v2/animals`, `/api/v2/adoptantes`, `/api/v2/adopciones` |

## Integrante C — Leonardo Giraldo (GCP)

| Campo | Valor |
|-------|--------|
| Repo | https://github.com/LeonardoG2005/MedicalDevops |
| URL base | `http://medical-documents-api-34-123-58-136.sslip.io` |
| Health | `GET /health` |
| Listas | `/imagenes`, `/notas-medicas`, `/documentos-generados` |

## Componentes transversales

| Rol | Responsable | Nube |
|-----|-------------|------|
| MS orquestador | (acordar; Leonardo tiene `orchestrator/` en su repo) | |
| Cola / DLQ | (acordar) | |
| Caché | (acordar) | |
| **Object storage + consumidor** | **Juan (A)** | **OCI** |

## Prueba conjunta

1. `POST /api/v2/flujo` con `X-Trace-Id` en la API A.  
2. Verificar `vinculos` con animal/imagen, adoptante/nota y adopción/documento.  
3. `GET /api/v2/storage/flujo/{trace_id}`.  
4. Cambiar un dato en B o C y repetir el flujo.
