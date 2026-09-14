from typing import Any, Protocol


class ObjectStorage(Protocol):
    backend: str
    bucket: str

    def put_json(self, object_key: str, payload: dict[str, Any]) -> None: ...

    def get_json(self, object_key: str) -> dict[str, Any]: ...

    def put_bytes(self, object_key: str, data: bytes, content_type: str) -> None: ...

    def get_bytes(self, object_key: str) -> tuple[bytes, str]: ...
