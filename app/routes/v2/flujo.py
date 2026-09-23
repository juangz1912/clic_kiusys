from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas_v2 import FlujoV2Request, FlujoV2Response, MensajeV2Request, MensajeV2Response
from app.services.v2_flow_service import append_api_a, build_flujo_v2

router = APIRouter()


@router.post("/flujo", response_model=FlujoV2Response)
def post_flujo_v2(
    payload: FlujoV2Request,
    request: Request,
    db: Session = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", "unknown")
    return build_flujo_v2(db, payload, trace_id)


@router.post("/mensaje", response_model=MensajeV2Response)
def post_mensaje_v2(
    payload: MensajeV2Request,
    request: Request,
    db: Session = Depends(get_db),
):
    """Contrato para el orquestador: agrega Vuelo, Pasajero y AsientoAsignado al mensaje."""
    trace_id = getattr(request.state, "trace_id", "unknown")
    return append_api_a(db, payload, trace_id)
