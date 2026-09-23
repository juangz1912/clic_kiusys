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

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/api/v2/health` | Health con metadata OCI/OKE y trace-id |
| POST | `/api/v2/flujo` | Vínculos: Vuelo–Animal–Imagen, Pasajero–Adoptante–NotaMedica, Asiento–Adopcion–DocumentoGenerado |
| GET | `/api/v2/metrics` | Métricas RED básicas por endpoint v2 |

Headers: **`X-Trace-Id`** (entrada/salida y llamadas a compañeros).

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
- Métricas v2 en `/api/v2/metrics`.
- Tablero SaaS grupal (Grafana/Datadog): configurar `OBSERVABILITY_SAAS_URL` en README cuando el equipo lo tenga.

## Checklist sustentación

- [ ] Demo `POST /api/v2/flujo` con URLs reales de B y C
- [ ] Cambio en dato de compañero reflejado en vivo
- [ ] 2+ réplicas en OKE y HPA visible
- [ ] Trace-id correlacionado en logs
- [ ] Tag **v2.0.0** y release en GitHub
