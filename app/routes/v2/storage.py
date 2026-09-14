from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response

from app.schemas_v2 import ObjectStorageRef
from app.services.object_storage_service import load_adjunto, load_flujo_snapshot, store_adjunto

router = APIRouter()


@router.get("/storage/flujo/{trace_id}")
def get_flujo_snapshot(trace_id: str):
    try:
        return load_flujo_snapshot(trace_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Snapshot de flujo no encontrado") from exc
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/storage/adjunto", response_model=ObjectStorageRef)
async def upload_adjunto(
    request: Request,
    file: UploadFile = File(...),
):
    trace_id = getattr(request.state, "trace_id", None) or request.headers.get("X-Trace-Id")
    if not trace_id:
        raise HTTPException(status_code=400, detail="Falta X-Trace-Id")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacio")
    content_type = file.content_type or "application/octet-stream"
    return store_adjunto(trace_id, file.filename or "adjunto.bin", data, content_type)


@router.get("/storage/adjunto/{trace_id}/{filename}")
def download_adjunto(trace_id: str, filename: str):
    try:
        data, content_type = load_adjunto(trace_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado") from exc
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{quote(filename)}"'},
    )
