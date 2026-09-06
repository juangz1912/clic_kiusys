from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas_v2 import FlujoV2Request, FlujoV2Response
from app.services.v2_flow_service import build_flujo_v2

router = APIRouter()


@router.post("/flujo", response_model=FlujoV2Response)
def post_flujo_v2(
    payload: FlujoV2Request,
    request: Request,
    db: Session = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", "unknown")
    return build_flujo_v2(db, payload, trace_id)
