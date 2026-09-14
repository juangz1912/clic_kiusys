# Datos para compartir con el equipo (Seguimiento #2)

Generar bloque listo para el chat:

```bash
./scripts/handoff_equipo.sh http://TU-IP-LB-OKE
# o mientras tanto:
./scripts/handoff_equipo.sh https://clic-kiusys-pruebas.onrender.com
```

## Integrante A — Juan (OCI / OKE + Object Storage)

| Campo | Valor |
|-------|--------|
| Repo | https://github.com/juangz1912/clic_kiusys |
| Nube | **Oracle OCI** |
| Rol transversal | **Object Storage** + consumidor (JSON flujo + adjuntos) |
| URL base API | `http://<IP-LoadBalancer-OKE>` (Render pruebas: https://clic-kiusys-pruebas.onrender.com) |
| Bucket OCI | `clic-kiusys-flow` (privado; acceso vía API A) |

### Endpoints v2 (header `X-Trace-Id` obligatorio)

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/api/v2/health` | Health + metadata OCI |
| POST | `/api/v2/flujo` | Agrega vuelo local + entidades HTTP B/C; **guarda JSON en Object Storage** |
| GET | `/api/v2/metrics` | Métricas RED v2 |
| GET | `/api/v2/entidades/vuelos` | **Consumir desde B/C** — lista de vuelos (entidad A) |
| GET | `/api/v2/storage/flujo/{trace_id}` | **Consumidor** — JSON acumulado del flujo |
| POST | `/api/v2/storage/adjunto` | Subir adjunto del mensaje (multipart + `X-Trace-Id`) |
| GET | `/api/v2/storage/adjunto/{trace_id}/{filename}` | Descargar adjunto |

Tras `POST /api/v2/flujo`, la respuesta incluye `object_storage.get_url` con la ruta GET del snapshot.

### Lo que necesito de ustedes

| Integrante | Entregar |
|------------|----------|
| **B (GCP)** | `URL base` pública + path GET lista (ej. `/api/mascotas`) |
| **C (Azure/AWS)** | `URL base` pública + path GET lista (ej. `/api/items`) |
| **Orquestador** (quien lo lleve) | Invocar las 3 APIs v2 y propagar `X-Trace-Id`; puede leer `GET .../storage/flujo/{trace_id}` |

Variables que yo configuro en OKE cuando me las pasen: `API_B_BASE_URL`, `API_C_BASE_URL`.

## Integrante B — GCP

| Campo | Valor |
|-------|--------|
| URL base | |
| Endpoint GET lista | |
| Entidad propia | (su Seguimiento #1) |

Debe consumir **≥1 entidad mía** vía HTTP, por ejemplo:  
`GET {URL_A}/api/v2/entidades/vuelos`

## Integrante C — Azure/AWS

| Campo | Valor |
|-------|--------|
| URL base | |
| Endpoint GET lista | |
| Entidad propia | (su Seguimiento #1) |

Misma regla: consumir vuelos desde mi URL pública.

## Componentes transversales

| Rol | Responsable | Nube |
|-----|-------------|------|
| MS orquestador | (acordar) | |
| Cola / DLQ | (acordar) | |
| Caché | (acordar) | |
| **Object storage + consumidor** | **Juan (A)** | **OCI** |

## Prueba conjunta (sustentación)

1. Orquestador (o Postman) dispara flujo en las 3 APIs con el mismo `X-Trace-Id`.  
2. `POST /api/v2/flujo` en OCI → ver companions + `object_storage.stored: true`.  
3. `GET /api/v2/storage/flujo/{trace_id}` → JSON acumulado.  
4. Cambiar dato en B o C → repetir flujo → debe reflejarse.  
5. Trace-id visible en logs de las 3 nubes; HPA en OKE.

## OCI — pasos que cierran tu parte

1. `./scripts/oci/07_create_bucket.sh` (bucket)  
2. Customer Secret Key → `oci.env` (`OCI_S3_*`, `OCI_OS_NAMESPACE`)  
3. `OBJECT_STORAGE_BACKEND=oci` en ConfigMap + `04_create_secret.sh`  
4. `./scripts/oci/deploy_all.sh` → anotar IP LB → `./scripts/handoff_equipo.sh http://IP`
