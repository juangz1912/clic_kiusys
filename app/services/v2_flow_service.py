from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients.api_b import fetch_all_b
from app.clients.api_c import fetch_all_c
from app.models.entities import AsientoAsignado, Pasajero, Vuelo
from app.schemas import AsientoAsignadoRead, PasajeroRead, VueloRead
from app.schemas_v2 import (
    CompanionPayload,
    FlujoV2Request,
    FlujoV2Response,
    MensajeV2Request,
    MensajeV2Response,
    VinculoPayload,
)
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


def _asiento_del_vuelo(db: Session, vuelo_id: int) -> AsientoAsignadoRead | None:
    row = (
        db.query(AsientoAsignado)
        .filter(AsientoAsignado.vuelo_id == vuelo_id)
        .order_by(AsientoAsignado.id.desc())
        .first()
    )
    return AsientoAsignadoRead.model_validate(row) if row else None


def _pasajero_del_asiento(db: Session, asiento: AsientoAsignadoRead | None) -> PasajeroRead | None:
    if not asiento or not asiento.pasajero_id:
        return None
    row = db.get(Pasajero, asiento.pasajero_id)
    return PasajeroRead.model_validate(row) if row else None


def api_a_block(db: Session, payload: FlujoV2Request) -> dict[str, Any]:
    vuelo = _resolve_local_vuelo(db, payload)
    asiento = _asiento_del_vuelo(db, vuelo.id)
    pasajero = _pasajero_del_asiento(db, asiento)
    return {
        "cloud": "oci",
        "vuelo": vuelo.model_dump(mode="json"),
        "pasajero": pasajero.model_dump(mode="json") if pasajero else None,
        "asiento_asignado": asiento.model_dump(mode="json") if asiento else None,
    }


def _payload(raw: dict[str, Any]) -> CompanionPayload:
    return CompanionPayload.model_validate(raw)


def build_flujo_v2(db: Session, payload: FlujoV2Request, trace_id: str) -> FlujoV2Response:
    local = _resolve_local_vuelo(db, payload)
    asiento = _asiento_del_vuelo(db, local.id)
    pasajero = _pasajero_del_asiento(db, asiento)

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


def append_api_a(db: Session, payload: MensajeV2Request, trace_id: str) -> MensajeV2Response:
    """El orquestador envía el mensaje; esta API agrega sus entidades y lo persiste."""
    bloque = api_a_block(
        db,
        FlujoV2Request(
            vuelo_id=payload.vuelo_id,
            origen=payload.origen,
            destino=payload.destino,
            fecha=payload.fecha,
        ),
    )
    mensaje = dict(payload.mensaje)
    pasos = list(mensaje.get("pasos") or [])
    pasos.append({"api": "api_a", "cloud": "oci", "trace_id": trace_id, "entidades": bloque})
    mensaje["pasos"] = pasos
    mensaje["api_a"] = bloque
    mensaje["trace_id"] = trace_id
    ref = store_flujo_snapshot(trace_id, mensaje)
    return MensajeV2Response(trace_id=trace_id, mensaje=mensaje, object_storage=ref)
