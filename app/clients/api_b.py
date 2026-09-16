from typing import Any

from app.clients.http_utils import fetch_remote_entity
from app.config import settings


def fetch_companion_entity_b(trace_id: str) -> dict[str, Any]:
    return fetch_animal(trace_id)


def fetch_animal(trace_id: str) -> dict[str, Any]:
    return fetch_remote_entity(
        "api_b_animal",
        settings.api_b_base_url,
        settings.api_b_animal_path,
        trace_id,
    )


def fetch_adoptante(trace_id: str) -> dict[str, Any]:
    return fetch_remote_entity(
        "api_b_adoptante",
        settings.api_b_base_url,
        settings.api_b_adoptante_path,
        trace_id,
    )


def fetch_adopcion(trace_id: str) -> dict[str, Any]:
    return fetch_remote_entity(
        "api_b_adopcion",
        settings.api_b_base_url,
        settings.api_b_adopcion_path,
        trace_id,
    )


def fetch_all_b(trace_id: str) -> dict[str, dict[str, Any]]:
    return {
        "animal": fetch_animal(trace_id),
        "adoptante": fetch_adoptante(trace_id),
        "adopcion": fetch_adopcion(trace_id),
    }
