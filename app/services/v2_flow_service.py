from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients.api_b import fetch_all_b
from app.clients.api_c import fetch_all_c
from app.models.entities import AsientoAsignado, Pasajero, Vuelo
from app.schemas import AsientoAsignadoRead, PasajeroRead, VueloRead
from app.schemas_v2 import CompanionPayload, FlujoV2Request, FlujoV2Response, VinculoPayload
from app.services.object_storage_service import store_flujo_snapshot


def _local_block(entity: str, data: Any | None) -> dict[str, Any]:
    return {"entity": entity, "data": data}


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


def _latest_pasajero(db: Session) -> PasajeroRead | None:
    row = db.query(Pasajero).order_by(Pasajero.id.desc()).first()
    return PasajeroRead.model_validate(row) if row else None


def _latest_asiento(db: Session) -> AsientoAsignadoRead | None:
    row = db.query(AsientoAsignado).order_by(AsientoAsignado.id.desc()).first()
    return AsientoAsignadoRead.model_validate(row) if row else None


def _payload(raw: dict[str, Any]) -> CompanionPayload:
    return CompanionPayload.model_validate(raw)


def build_flujo_v2(db: Session, payload: FlujoV2Request, trace_id: str) -> FlujoV2Response:
    local = _resolve_local_vuelo(db, payload)
    pasajero = _latest_pasajero(db)
    asiento = _latest_asiento(db)

    b_raw = fetch_all_b(trace_id)
    c_raw = fetch_all_c(trace_id)

    vinculos = [
        VinculoPayload(
            rol="vuelo-animal-imagen",
            local=_local_block("vuelo", local.model_dump(mode="json")),
            api_b=_payload(b_raw["animal"]),
            api_c=_payload(c_raw["imagen"]),
        ),
        VinculoPayload(
            rol="pasajero-adoptante-nota",
            local=_local_block(
                "pasajero",
                pasajero.model_dump(mode="json") if pasajero else None,
            ),
            api_b=_payload(b_raw["adoptante"]),
            api_c=_payload(c_raw["nota_medica"]),
        ),
        VinculoPayload(
            rol="asiento-adopcion-documento",
            local=_local_block(
                "asiento_asignado",
                asiento.model_dump(mode="json") if asiento else None,
            ),
            api_b=_payload(b_raw["adopcion"]),
            api_c=_payload(c_raw["documento_generado"]),
        ),
    ]

    companions = [
        vinculos[0].api_b,
        vinculos[0].api_c,
        vinculos[1].api_b,
        vinculos[1].api_c,
        vinculos[2].api_b,
        vinculos[2].api_c,
    ]

    local_block = vinculos[0].local

    snapshot = {
        "trace_id": trace_id,
        "api_version": "v2",
        "local": local_block,
        "vinculos": [v.model_dump(mode="json") for v in vinculos],
        "companions": [c.model_dump(mode="json") for c in companions],
    }

    return FlujoV2Response(
        trace_id=trace_id,
        local=local_block,
        companions=companions,
        vinculos=vinculos,
        object_storage=store_flujo_snapshot(trace_id, snapshot),
    )
