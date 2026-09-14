"""APIs mínimas B (GCP) y C (Azure/AWS) para demo multicloud sin depender del equipo."""

import uuid

from fastapi import FastAPI, Request, Response

app = FastAPI(title="Companion mocks B/C", version="1.0.0")
TRACE_HEADER = "X-Trace-Id"


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get(TRACE_HEADER) or str(uuid.uuid4())
    response: Response = await call_next(request)
    response.headers[TRACE_HEADER] = trace_id
    return response


@app.get("/api/health")
def health():
    return {"status": "ok", "role": "companion-mocks"}


@app.get("/api/mascotas")
def list_mascotas(request: Request):
    trace_id = request.headers.get(TRACE_HEADER, "")
    return [
        {
            "id": 9001,
            "nombre": "Mock GCP — entidad demo",
            "especie": "demo",
            "cloud": "gcp",
            "trace_id": trace_id,
        }
    ]


@app.get("/api/items")
def list_items(request: Request):
    trace_id = request.headers.get(TRACE_HEADER, "")
    return [
        {
            "id": 7001,
            "nombre": "Mock Azure/AWS — ítem demo",
            "grupo_id": 1,
            "cloud": "azure-aws",
            "trace_id": trace_id,
        }
    ]
