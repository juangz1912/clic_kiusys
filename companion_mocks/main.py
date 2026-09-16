"""Mocks locales de las rutas reales de Angel y Leonardo (offline)."""

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


@app.get("/api/v2/animals")
def list_animals(request: Request):
    trace_id = request.headers.get(TRACE_HEADER, "")
    return {
        "data": [
            {
                "id": 9001,
                "nombre": "Mock animal",
                "especie": "Perro",
                "trace_id": trace_id,
            }
        ],
        "traceId": trace_id,
    }


@app.get("/api/v2/adoptantes")
def list_adoptantes(request: Request):
    trace_id = request.headers.get(TRACE_HEADER, "")
    return {"data": [{"id": 8001, "nombre": "Mock adoptante", "trace_id": trace_id}], "traceId": trace_id}


@app.get("/api/v2/adopciones")
def list_adopciones(request: Request):
    trace_id = request.headers.get(TRACE_HEADER, "")
    return {"data": [{"id": 7001, "estado": "ACTIVA", "trace_id": trace_id}], "traceId": trace_id}


@app.get("/imagenes")
def list_imagenes(request: Request):
    return [{"id": 1, "nombre": "Mock imagen", "url": "https://example.com/img.jpg"}]


@app.get("/notas-medicas")
def list_notas(request: Request):
    return [{"id": 1, "paciente": "Mock paciente", "contenido": "nota demo"}]


@app.get("/documentos-generados")
def list_docs(request: Request):
    return [{"id": 1, "nombre": "Mock documento", "tipo": "pdf"}]
