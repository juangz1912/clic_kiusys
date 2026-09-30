# Consumidor del Object Storage

Artefacto propio del componente Object Storage (Integrante A, OCI). Corre en OKE como un Deployment de una réplica, separado de la API.

## Qué hace

1. Cada `POLL_SECONDS` (15 s) lista `flujo/*.json` en el bucket `clic-kiusys-flow`. Esos objetos los escribe la API A cuando el orquestador le entrega el mensaje (`POST /api/v2/mensaje`) o cuando se llama `POST /api/v2/flujo`.
2. Por cada mensaje sin resumen genera `adjuntos/<trace_id>/resumen.md`: una tabla con los pasos del mensaje (API, nube y entidad agregada).
3. Registra cada resumen en stdout como JSON con el `trace_id`, así que aparece en OCI Logging junto a los logs de la API.

```
orquestador (GCP) -> API A (OCI) -> bucket flujo/<trace_id>.json -> consumidor -> bucket adjuntos/<trace_id>/resumen.md
```

## Cómo usarlo

Después de un flujo, el adjunto se descarga por la API:

```bash
curl http://157-137-193-66.sslip.io/api/v2/storage/adjunto/<trace_id>/resumen.md
```

Logs del consumidor:

```bash
kubectl -n clic-kiusys logs deploy/clic-kiusys-storage-consumer --since=10m
```

## Configuración

| Variable | Origen |
|----------|--------|
| `OCI_OS_NAMESPACE`, `OCI_OS_REGION`, `OCI_OS_BUCKET` | ConfigMap `clic-kiusys-api-config` |
| `OCI_S3_ACCESS_KEY_ID`, `OCI_S3_SECRET_ACCESS_KEY` | Secret `clic-kiusys-api-secret` (Customer Secret Key de OCI, API compatible con S3) |
| `POLL_SECONDS` | Manifiesto (15) |

La liveness probe revisa que el ciclo haya tocado `/tmp/consumer-heartbeat` en los últimos 2 minutos.

## Contenedor y pipeline

- Imagen: `sa-bogota-1.ocir.io/ax5bqkfrllcm/clic-kiusys-storage-consumer:<sha>` (`storage_consumer/Dockerfile`).
- Manifiesto: `k8s/storage-consumer.yaml`.
- Pipeline: `.github/workflows/deploy-storage-consumer.yml`. Corre en cada push a `main` que toque `storage_consumer/` o el manifiesto: pruebas, build, push a OCIR y rollout en OKE.

## Pruebas locales

```bash
cd storage_consumer
pip install -r requirements.txt pytest
pytest -q
```
