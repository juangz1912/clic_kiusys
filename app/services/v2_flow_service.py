from datetime import date
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients.api_b import fetch_companion_entity_b
from app.clients.api_c import fetch_companion_entity_c
from app.models.entities import Vuelo
from app.schemas import VueloRead
from app.schemas_v2 import CompanionPayload, FlujoV2Request, FlujoV2Response
from app.services.object_storage_service import store_flujo_snapshot


def _resolve_local_vuelo(db: Session, payload: FlujoV2Request) -> VueloRead:
    if payload.vuelo_id:
        vuelo = db.get(Vuelo, payload.vuelo_id)
        if not vuelo:
            raise HTTPException(status_code=404, detail="Vuelo no encontrado")
        return VueloRead.model_validate(vuelo)

    query = db.query(Vuelo)
    if payload.origen:
        query = query.filter(Vuelo.origen == payload.origen.upper())
    if payload.destino:
        query = query.filter(Vuelo.destino == payload.destino.upper())
    if payload.fecha:
        query = query.filter(Vuelo.fecha == payload.fecha)

    vuelo = query.order_by(Vuelo.id.desc()).first()
    if not vuelo:
        raise HTTPException(
            status_code=404,
            detail="No hay vuelo local; crea uno en v1 o envia vuelo_id",
        )
    return VueloRead.model_validate(vuelo)


def build_flujo_v2(db: Session, payload: FlujoV2Request, trace_id: str) -> FlujoV2Response:
    local = _resolve_local_vuelo(db, payload)
    b_raw = fetch_companion_entity_b(trace_id)
    c_raw = fetch_companion_entity_c(trace_id)

    companions = [
        CompanionPayload.model_validate(b_raw),
        CompanionPayload.model_validate(c_raw),
    ]

    local_block: dict[str, Any] = {
        "entity": "vuelo",
        "data": local.model_dump(mode="json"),
    }

    return FlujoV2Response(
        trace_id=trace_id,
        local=local_block,
        companions=companions,
        object_storage=store_flujo_snapshot(
            trace_id,
            {
                "trace_id": trace_id,
                "api_version": "v2",
                "local": local_block,
                "companions": [c.model_dump(mode="json") for c in companions],
            },
        ),
    )
