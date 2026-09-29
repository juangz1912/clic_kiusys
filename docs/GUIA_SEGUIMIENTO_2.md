# Guía Seguimiento #2 — Multicloud (Integrante A / OCI)

Repositorio: https://github.com/juangz1912/clic_kiusys  
Sustentación: acordada con el grupo (el PDF original decía 16 de septiembre de 2026).

## Equipo y nubes

| Integrante | Nube | Componente principal |
|------------|------|----------------------|
| Juan Jose Giraldo | **Oracle OCI** | API A en **OKE** (Vuelo, Pasajero, AsientoAsignado) + Object Storage |
| Angel Avirama | **AWS** | API B adopción (`/api/v2/animals`, `/api/v2/adoptantes`, `/api/v2/adopciones`) |
| Leonardo Giraldo | **GCP** | API C documentos (`/imagenes`, `/notas-medicas`, `/documentos-generados`) |

Componentes transversales (1 por integrante, nube distinta): orquestador, caché, object storage.

Diagrama de referencia: `Arquitectura_Multicloud_Seguimiento2_2026-2.png` (carpeta devops del equipo).

## API v2 (esta entrega)

Contrato del grupo: un GET random por entidad y un GET por id que trae una entidad random de cada compañero.

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/api/v2/entidades/vuelos/random` | Vuelo random (lo consumen Angel y Leonardo) |
| GET | `/api/v2/entidades/pasajeros/random` | Pasajero random |
| GET | `/api/v2/entidades/asientos-asignados/random` | Asiento asignado random |
| GET | `/api/v2/entidades/vuelos/{id}` | Vuelo + Animal random (Angel, AWS) + Imagen random (Leonardo, GCP) |
| POST | `/api/v2/flujo` | Vínculos: Vuelo–Animal–Imagen, Pasajero–Adoptante–NotaMedica, Asiento–Adopcion–DocumentoGenerado |
| POST | `/api/v2/mensaje` | Agrega Vuelo, Asiento y Pasajero al mensaje del orquestador y lo guarda en Object Storage |
| GET | `/api/v2/storage/flujo` | Lista los snapshots guardados en el bucket |
| GET | `/api/v2/health` | Health con metadata OCI/OKE y trace-id |
| GET | `/api/v2/metrics` | Métricas RED (requests, errores, p50, p95) por endpoint v2 |
| GET | `/api/v2/demo/fallo` | 500 a propósito para la demo de alerta (`DEMO_FAILURE_ENABLED=true`) |

Headers: **`X-Trace-Id`** y **`traceparent`** (entrada/salida y llamadas a compañeros).

Links listos para la sustentación: sección [Links de sustentación](../README.md#links-de-sustentación) del README.

Variables `.env`:

- `API_B_BASE_URL` (Angel, AWS), `API_B_ANIMAL_PATH`, `API_B_ADOPTANTE_PATH`, `API_B_ADOPCION_PATH`
- `API_C_BASE_URL` (Leonardo, GCP), `API_C_IMAGEN_PATH`, `API_C_NOTA_PATH`, `API_C_DOCUMENTO_PATH`
- `INTEGRATION_STUB_WHEN_UNREACHABLE=false` en demos con las APIs reales; `true` para tests locales

## Probar en local

```bash
docker compose up -d
pytest --cov=app --cov-report=term-missing
python scripts/test_v2_endpoints.py http://localhost:8001
```

Swagger: http://localhost:8001/docs → sección **v2**.

## Despliegue OKE (OCI)

1. Crear cluster **OKE** y conectar `kubectl`.
2. Postgres en el cluster (`k8s/postgres.yaml`, block volume) y `DATABASE_URL` en Secret.
3. Copiar `k8s/secret.yaml.example` → aplicar Secret con URLs reales de B/C.
4. Build/push imagen Docker del `Dockerfile`.
5. Actualizar imagen en `k8s/deployment.yaml`.
6. `./scripts/k8s_apply.sh`
7. Verificar: `kubectl -n clic-kiusys get pods,hpa,ingress`
8. OCI Monitoring + Logging sobre el cluster y la API.

## Observabilidad

- Logs de la app incluyen `trace_id`.
- Métricas v2 en `/api/v2/metrics` y en Grafana Cloud por OpenTelemetry.
- Tablero del grupo: https://browngecko19.grafana.net/d/clic-s2-red/multicloud-s2-red-por-api
- Alerta Grafana "API A - errores 5xx" (correo) y alarma OCI `clic-kiusys-oke-cpu-alta`.
- Detalle: [OBSERVABILITY.md](OBSERVABILITY.md)

## Checklist sustentación

- [x] Random por entidad y `GET /api/v2/entidades/vuelos/{id}` con Angel en vivo
- [x] Imagen random de Leonardo (`/api/v2/imagenes/random`)
- [x] 2+ réplicas en OKE y HPA 2 a 5 (`scripts/k8s_hpa_demo.sh`)
- [x] Trace-id en respuesta, logs y trazas de Grafana
- [x] Object Storage en bucket OCI `clic-kiusys-flow`
- [x] Tablero RED (rate, errores, p50/p95) en Grafana Cloud
- [x] Alerta que se dispara en vivo (`scripts/demo_alerta.sh`)
- [x] Alarma nativa de OCI Monitoring
- [x] Tag **v2.2.1** y release en GitHub
- [ ] Angel y Leonardo exportando a Grafana con su `OTEL_SERVICE_NAME`
- [ ] Caché y cola con métricas (dueños: compañeros)
