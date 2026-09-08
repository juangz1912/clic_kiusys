from unittest.mock import MagicMock, patch

from app.clients.api_c import fetch_companion_entity_c


def test_fetch_api_c_not_configured():
    with patch("app.clients.api_c.settings") as mock_settings:
        mock_settings.api_c_base_url = ""
        result = fetch_companion_entity_c("trace-1")
    assert result["configured"] is False


def test_fetch_api_c_error_returns_stub_payload():
    with patch("app.clients.api_c.settings") as mock_settings:
        mock_settings.api_c_base_url = "https://c.example.com"
        mock_settings.api_c_entity_path = "/api/items"
        mock_settings.integration_timeout_seconds = 5.0
        mock_settings.integration_stub_when_unreachable = True
        with patch("app.clients.api_c.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.get.side_effect = TimeoutError("timeout")
            mock_client_cls.return_value = mock_client
            result = fetch_companion_entity_c("trace-3")

    assert result["configured"] is True
    assert result["entity"] is None
    assert "error" in result
