from typing import Any

from app.clients.http_utils import fetch_remote_entity
from app.config import settings


def fetch_companion_entity_c(trace_id: str) -> dict[str, Any]:
    return fetch_imagen(trace_id)


def fetch_imagen(trace_id: str) -> dict[str, Any]:
    return fetch_remote_entity(
        "api_c_imagen",
        settings.api_c_base_url,
        settings.api_c_imagen_path,
        trace_id,
    )


def fetch_nota_medica(trace_id: str) -> dict[str, Any]:
    return fetch_remote_entity(
        "api_c_nota",
        settings.api_c_base_url,
        settings.api_c_nota_path,
        trace_id,
    )


def fetch_documento_generado(trace_id: str) -> dict[str, Any]:
    return fetch_remote_entity(
        "api_c_documento",
        settings.api_c_base_url,
        settings.api_c_documento_path,
        trace_id,
    )


def fetch_all_c(trace_id: str) -> dict[str, dict[str, Any]]:
    return {
        "imagen": fetch_imagen(trace_id),
        "nota_medica": fetch_nota_medica(trace_id),
        "documento_generado": fetch_documento_generado(trace_id),
    }
