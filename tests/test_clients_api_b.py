from unittest.mock import MagicMock, patch

from app.clients.api_b import fetch_companion_entity_b


def test_fetch_api_b_not_configured():
    with patch("app.clients.api_b.settings") as mock_settings:
        mock_settings.api_b_base_url = ""
        result = fetch_companion_entity_b("trace-1")
    assert result["configured"] is False
    assert result["entity"] is None


def test_fetch_api_b_success():
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 1, "nombre": "MascotaX"}]
    mock_response.raise_for_status = MagicMock()

    with patch("app.clients.api_b.settings") as mock_settings:
        mock_settings.api_b_base_url = "https://b.example.com"
        mock_settings.api_b_entity_path = "/api/mascotas"
        mock_settings.integration_timeout_seconds = 5.0
        mock_settings.integration_stub_when_unreachable = True
        with patch("app.clients.api_b.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client
            result = fetch_companion_entity_b("trace-2")

    assert result["configured"] is True
    assert result["entity"]["nombre"] == "MascotaX"
