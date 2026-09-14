import json
from pathlib import Path
from typing import Any


class LocalObjectStorage:
    backend = "local"

    def __init__(self, root_dir: str, bucket_label: str = "local"):
        self.bucket = bucket_label
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, object_key: str) -> Path:
        safe = object_key.lstrip("/").replace("..", "_")
        path = self.root / safe
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def put_json(self, object_key: str, payload: dict[str, Any]) -> None:
        self._path(object_key).write_text(
            json.dumps(payload, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def get_json(self, object_key: str) -> dict[str, Any]:
        path = self._path(object_key)
        if not path.exists():
            raise FileNotFoundError(object_key)
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("object is not a JSON object")
        return data

    def put_bytes(self, object_key: str, data: bytes, content_type: str) -> None:
        path = self._path(object_key)
        path.write_bytes(data)
        meta = path.with_suffix(path.suffix + ".meta")
        meta.write_text(content_type, encoding="utf-8")

    def get_bytes(self, object_key: str) -> tuple[bytes, str]:
        path = self._path(object_key)
        if not path.exists():
            raise FileNotFoundError(object_key)
        meta = path.with_suffix(path.suffix + ".meta")
        content_type = meta.read_text(encoding="utf-8") if meta.exists() else "application/octet-stream"
        return path.read_bytes(), content_type
