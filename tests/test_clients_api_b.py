from unittest.mock import MagicMock, patch

from app.clients.api_b import fetch_adoptante, fetch_animal, fetch_companion_entity_b
from app.clients.http_utils import unwrap_entity


def test_unwrap_entity_from_data_wrapper():
    payload = {"data": [{"id": 2, "nombre": "Sofi"}], "traceId": "abc"}
    assert unwrap_entity(payload)["nombre"] == "Sofi"


def test_unwrap_entity_from_list():
    assert unwrap_entity([{"id": 1}])["id"] == 1


def test_fetch_api_b_not_configured():
    with patch("app.clients.http_utils.settings") as mock_settings:
        mock_settings.integration_timeout_seconds = 5.0
        mock_settings.integration_stub_when_unreachable = True
        with patch("app.clients.api_b.settings") as b_settings:
            b_settings.api_b_base_url = ""
            b_settings.api_b_animal_path = "/api/v2/animals"
            result = fetch_companion_entity_b("trace-1")
    assert result["configured"] is False
    assert result["entity"] is None


def test_fetch_animal_unwraps_data_wrapper():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [{"id": 2, "nombre": "Sofi", "especie": "Perro"}],
        "traceId": "trace-2",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.clients.http_utils.settings") as mock_settings:
        mock_settings.integration_timeout_seconds = 5.0
        mock_settings.integration_stub_when_unreachable = False
        with patch("app.clients.api_b.settings") as b_settings:
            b_settings.api_b_base_url = "https://b.example.com"
            b_settings.api_b_animal_path = "/api/v2/animals"
            with patch("app.clients.http_utils.httpx.Client") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.__enter__.return_value = mock_client
                mock_client.get.return_value = mock_response
                mock_client_cls.return_value = mock_client
                result = fetch_animal("trace-2")

    assert result["configured"] is True
    assert result["source"] == "api_b_animal"
    assert result["entity"]["nombre"] == "Sofi"
    assert result["url"] == "https://b.example.com/api/v2/animals"


def test_fetch_adoptante_path():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"id": 9, "nombre": "Ana"}]}
    mock_response.raise_for_status = MagicMock()

    with patch("app.clients.http_utils.settings") as mock_settings:
        mock_settings.integration_timeout_seconds = 5.0
        mock_settings.integration_stub_when_unreachable = False
        with patch("app.clients.api_b.settings") as b_settings:
            b_settings.api_b_base_url = "https://b.example.com"
            b_settings.api_b_adoptante_path = "/api/v2/adoptantes"
            with patch("app.clients.http_utils.httpx.Client") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.__enter__.return_value = mock_client
                mock_client.get.return_value = mock_response
                mock_client_cls.return_value = mock_client
                result = fetch_adoptante("trace-4")

    assert result["url"] == "https://b.example.com/api/v2/adoptantes"
    assert result["entity"]["nombre"] == "Ana"
