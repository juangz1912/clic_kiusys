from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.schemas import VueloRead


class FlujoV2Request(BaseModel):
    vuelo_id: int | None = None
    origen: str | None = Field(default=None, min_length=3, max_length=3)
    destino: str | None = Field(default=None, min_length=3, max_length=3)
    fecha: date | None = None


class CompanionPayload(BaseModel):
    source: str
    configured: bool
    entity: dict[str, Any] | list[Any] | None = None
    error: str | None = None
    url: str | None = None


class FlujoV2Response(BaseModel):
    trace_id: str
    api_version: str = "v2"
    local: dict[str, Any]
    companions: list[CompanionPayload]
    object_storage: "ObjectStorageRef | None" = None


class ObjectStorageRef(BaseModel):
    backend: str
    bucket: str
    object_key: str
    get_url: str
    stored: bool


FlujoV2Response.model_rebuild()


class HealthV2Response(BaseModel):
    status: str
    service: str
    api_version: str = "v2"
    environment: str
    cloud_provider: str
    oke_cluster_name: str
    trace_id: str
