"""Consumidor del Object Storage de OCI.

Revisa el bucket cada POLL_SECONDS. Por cada mensaje del flujo (flujo/<trace_id>.json) que todavía
no tenga resumen, genera el adjunto adjuntos/<trace_id>/resumen.md y lo sube al mismo bucket.
La API lo sirve en GET /api/v2/storage/adjunto/<trace_id>/resumen.md.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

FLUJO_PREFIX = "flujo/"
ADJUNTO_PREFIX = "adjuntos/"
RESUMEN = "resumen.md"
HEARTBEAT = Path(os.getenv("HEARTBEAT_FILE", "/tmp/consumer-heartbeat"))

logger = logging.getLogger("storage_consumer")


class Bucket(Protocol):
    def list_keys(self, prefix: str) -> list[str]: ...
    def get_json(self, key: str) -> dict[str, Any]: ...
    def put_text(self, key: str, text: str, content_type: str) -> None: ...


class OciBucket:
    """Bucket de OCI por la API compatible con S3 (mismas credenciales que la API A)."""

    def __init__(self, namespace: str, bucket: str, region: str, access_key: str, secret_key: str):
        import boto3
        from botocore.client import Config

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=f"https://{namespace}.compat.objectstorage.{region}.oraclecloud.com",
            config=Config(signature_version="s3v4"),
        )

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        token = None
        while True:
            kwargs: dict[str, Any] = {"Bucket": self.bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            page = self.client.list_objects_v2(**kwargs)
            keys.extend(item["Key"] for item in page.get("Contents") or [])
            if not page.get("IsTruncated"):
                return keys
            token = page.get("NextContinuationToken")

    def get_json(self, key: str) -> dict[str, Any]:
        body = self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        return json.loads(body.decode("utf-8"))

    def put_text(self, key: str, text: str, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=text.encode("utf-8"), ContentType=content_type)


def trace_id_from_key(key: str) -> str | None:
    if not key.startswith(FLUJO_PREFIX) or not key.endswith(".json"):
        return None
    return key[len(FLUJO_PREFIX) : -len(".json")] or None


def _entidad(paso: dict[str, Any]) -> Any:
    entidad = paso.get("entidad", paso.get("entidades"))
    if isinstance(entidad, dict) and isinstance(entidad.get("data"), dict):
        return entidad["data"]
    return entidad


def _describir(entidad: Any) -> str:
    if not isinstance(entidad, dict):
        return str(entidad)
    if "vuelo" in entidad:
        partes = [f"{k}: {_describir(v)}" for k, v in entidad.items() if isinstance(v, dict)]
        return "; ".join(partes)
    campos = ("id", "numero_vuelo", "nombre", "especie", "origen", "destino", "fecha", "paciente", "tipo", "estado")
    return ", ".join(f"{c}={entidad[c]}" for c in campos if entidad.get(c) is not None)


def render_resumen(trace_id: str, mensaje: dict[str, Any]) -> str:
    lineas = [
        f"# Resumen del mensaje {trace_id}",
        "",
        f"- Generado: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Estado: {mensaje.get('status', 'sin estado')}",
        "",
        "| # | API | Nube | Entidad |",
        "|---|-----|------|---------|",
    ]
    for i, paso in enumerate(mensaje.get("pasos") or [], start=1):
        lineas.append(f"| {i} | {paso.get('api', '?')} | {paso.get('cloud', '?')} | {_describir(_entidad(paso))} |")
    return "\n".join(lineas) + "\n"


def procesar(bucket: Bucket, ya_procesados: set[str]) -> list[str]:
    nuevos: list[str] = []
    for key in bucket.list_keys(FLUJO_PREFIX):
        trace_id = trace_id_from_key(key)
        if not trace_id or trace_id in ya_procesados:
            continue
        try:
            mensaje = bucket.get_json(key)
            bucket.put_text(f"{ADJUNTO_PREFIX}{trace_id}/{RESUMEN}", render_resumen(trace_id, mensaje), "text/markdown; charset=utf-8")
        except Exception:
            logger.exception(json.dumps({"event": "resumen_error", "trace_id": trace_id}))
            continue
        ya_procesados.add(trace_id)
        nuevos.append(trace_id)
        logger.info(json.dumps({"event": "resumen_generado", "trace_id": trace_id, "object_key": f"{ADJUNTO_PREFIX}{trace_id}/{RESUMEN}"}))
    return nuevos


def resumenes_existentes(bucket: Bucket) -> set[str]:
    hechos = set()
    for key in bucket.list_keys(ADJUNTO_PREFIX):
        partes = key[len(ADJUNTO_PREFIX) :].split("/")
        if len(partes) == 2 and partes[1] == RESUMEN:
            hechos.add(partes[0])
    return hechos


def bucket_desde_entorno() -> OciBucket:
    return OciBucket(
        namespace=os.environ["OCI_OS_NAMESPACE"],
        bucket=os.getenv("OCI_OS_BUCKET", "clic-kiusys-flow"),
        region=os.environ["OCI_OS_REGION"],
        access_key=os.environ["OCI_S3_ACCESS_KEY_ID"],
        secret_key=os.environ["OCI_S3_SECRET_ACCESS_KEY"],
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    poll = float(os.getenv("POLL_SECONDS", "15"))
    bucket = bucket_desde_entorno()
    procesados = resumenes_existentes(bucket)
    logger.info(json.dumps({"event": "inicio", "resumenes_existentes": len(procesados), "poll_seconds": poll}))
    while True:
        try:
            procesar(bucket, procesados)
            HEARTBEAT.touch()
        except Exception:
            logger.exception(json.dumps({"event": "ciclo_error"}))
        time.sleep(poll)


if __name__ == "__main__":
    main()
