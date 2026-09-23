from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.schemas import VueloRead


class FlujoV2Request(BaseModel):
    vuelo_id: int | None = None
    origen: str | None = Field(default=None, min_length=3, max_length=3)
    destino: str | None = Field(default=None, min_length=3, max_length=3)
    fecha: date | None = None


class MensajeV2Request(BaseModel):
    """Mensaje acumulado que envía el orquestador. Esta API le agrega api_a."""

    mensaje: dict[str, Any] = Field(default_factory=dict)
    vuelo_id: int | None = None
    origen: str | None = Field(default=None, min_length=3, max_length=3)
    destino: str | None = Field(default=None, min_length=3, max_length=3)
    fecha: date | None = None


class MensajeV2Response(BaseModel):
    trace_id: str
    api_version: str = "v2"
    mensaje: dict[str, Any]
    object_storage: "ObjectStorageRef | None" = None


class CompanionPayload(BaseModel):
    source: str
    configured: bool
    entity: dict[str, Any] | list[Any] | None = None
    error: str | None = None
    url: str | None = None


class VinculoPayload(BaseModel):
    rol: str
    local: dict[str, Any]
    api_b: CompanionPayload
    api_c: CompanionPayload


class FlujoV2Response(BaseModel):
    trace_id: str
    api_version: str = "v2"
    local: dict[str, Any]
    companions: list[CompanionPayload]
    vinculos: list[VinculoPayload] = Field(default_factory=list)
    object_storage: "ObjectStorageRef | None" = None


class ObjectStorageRef(BaseModel):
    backend: str
    bucket: str
    object_key: str
    get_url: str
    stored: bool


FlujoV2Response.model_rebuild()
MensajeV2Response.model_rebuild()


class HealthV2Response(BaseModel):
    status: str
    service: str
    api_version: str = "v2"
    environment: str
    cloud_provider: str
    oke_cluster_name: str
    trace_id: str
