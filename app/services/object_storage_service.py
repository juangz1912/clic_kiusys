from typing import Any

from app.config import settings
from app.schemas_v2 import ObjectStorageRef
from app.storage import get_object_storage

FLUJO_PREFIX = "flujo"
ADJUNTO_PREFIX = "adjuntos"


def flujo_object_key(trace_id: str) -> str:
    return f"{FLUJO_PREFIX}/{trace_id}.json"


def adjunto_object_key(trace_id: str, filename: str) -> str:
    safe_name = filename.replace("/", "_").replace("..", "_") or "adjunto.bin"
    return f"{ADJUNTO_PREFIX}/{trace_id}/{safe_name}"


def consumer_get_path(trace_id: str) -> str:
    return f"/api/v2/storage/flujo/{trace_id}"


def store_flujo_snapshot(trace_id: str, payload: dict[str, Any]) -> ObjectStorageRef:
    storage = get_object_storage()
    key = flujo_object_key(trace_id)
    storage.put_json(key, payload)
    base = settings.public_api_base_url.rstrip("/")
    get_url = f"{base}{consumer_get_path(trace_id)}" if base else consumer_get_path(trace_id)
    return ObjectStorageRef(
        backend=storage.backend,
        bucket=storage.bucket,
        object_key=key,
        get_url=get_url,
        stored=True,
    )


def load_flujo_snapshot(trace_id: str) -> dict[str, Any]:
    storage = get_object_storage()
    return storage.get_json(flujo_object_key(trace_id))


def store_adjunto(trace_id: str, filename: str, data: bytes, content_type: str) -> ObjectStorageRef:
    storage = get_object_storage()
    key = adjunto_object_key(trace_id, filename)
    storage.put_bytes(key, data, content_type)
    base = settings.public_api_base_url.rstrip("/")
    get_url = f"{base}/api/v2/storage/adjunto/{trace_id}/{filename}" if base else f"/api/v2/storage/adjunto/{trace_id}/{filename}"
    return ObjectStorageRef(
        backend=storage.backend,
        bucket=storage.bucket,
        object_key=key,
        get_url=get_url,
        stored=True,
    )


def load_adjunto(trace_id: str, filename: str) -> tuple[bytes, str]:
    storage = get_object_storage()
    return storage.get_bytes(adjunto_object_key(trace_id, filename))


def list_flujo_snapshots() -> list[dict[str, str]]:
    storage = get_object_storage()
    items = []
    for key in storage.list_keys(f"{FLUJO_PREFIX}/"):
        name = key.rsplit("/", 1)[-1]
        if not name.endswith(".json"):
            continue
        items.append({"trace_id": name[: -len(".json")], "object_key": key, "backend": storage.backend})
    return items
