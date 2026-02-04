"""Test request routing functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException
import httpx
from src.router import OllamaRouter
from src.config import Config, OllamaConfig, RouteConfig


class TestOllamaRouter:
    """Tests for OllamaRouter."""

    def test_init_with_config(self):
        """Test OllamaRouter initialization with config."""
        config = Config(ollama=OllamaConfig(base_url="http://test:11434"))
        router = OllamaRouter(config)

        assert router.config == config
        assert router.ollama_config.base_url == "http://test:11434"

    @pytest.mark.asyncio
    async def test_get_timeout_for_path_with_route_config(self):
        """Test getting timeout for a path with route-specific config."""
        config = Config(
            ollama=OllamaConfig(timeout=600),
            routes=[RouteConfig(path="/v1/models", timeout=30)],
        )
        router = OllamaRouter(config)

        timeout = await router.get_timeout_for_path("/v1/models")
        assert timeout == 30

    @pytest.mark.asyncio
    async def test_get_timeout_for_path_default(self):
        """Test getting default timeout for a path without route config."""
        config = Config(ollama=OllamaConfig(timeout=600))
        router = OllamaRouter(config)

        timeout = await router.get_timeout_for_path("/v1/unknown")
        assert timeout == 600

    @pytest.mark.asyncio
    async def test_proxy_request_success(self):
        """Test successful request proxying."""
        config = Config(ollama=OllamaConfig())
        router = OllamaRouter(config)

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.body = AsyncMock(return_value=b"test-body")

        # Mock httpx response
        mock_response = Mock()
        mock_response.content = b"response-content"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}

        # Mock the client.request call
        router.client.request = AsyncMock(return_value=mock_response)

        response = await router.proxy_request(mock_request, "/v1/models", b"test-body")

        assert response.status_code == 200
        assert response.body == b"response-content"
        router.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_proxy_request_timeout(self):
        """Test request proxying with timeout error."""
        config = Config(ollama=OllamaConfig())
        router = OllamaRouter(config)

        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.body = AsyncMock(return_value=b"")

        # Mock timeout exception
        router.client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with pytest.raises(HTTPException) as exc_info:
            await router.proxy_request(mock_request, "/v1/models")

        assert exc_info.value.status_code == 504
        assert "timed out" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_proxy_request_connection_error(self):
        """Test request proxying with connection error."""
        config = Config(ollama=OllamaConfig())
        router = OllamaRouter(config)

        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.body = AsyncMock(return_value=b"")

        # Mock connection error
        router.client.request = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(HTTPException) as exc_info:
            await router.proxy_request(mock_request, "/v1/models")

        assert exc_info.value.status_code == 502
        assert "Could not connect" in str(exc_info.value.detail)

    def test_filter_headers_removes_hop_by_hop(self):
        """Test that _filter_headers removes hop-by-hop headers."""
        config = Config(ollama=OllamaConfig())
        router = OllamaRouter(config)

        headers = {
            "content-type": "application/json",
            "connection": "keep-alive",
            "keep-alive": "timeout=5",
            "transfer-encoding": "chunked",
            "x-custom": "custom-value",
        }

        filtered = router._filter_headers(headers)

        assert "content-type" in filtered
        assert "x-custom" in filtered
        assert "connection" not in filtered
        assert "keep-alive" not in filtered
        assert "transfer-encoding" not in filtered

    def test_filter_headers_skips_content_length_for_streaming(self):
        """Test that _filter_headers skips content-length for streaming responses."""
        config = Config(ollama=OllamaConfig())
        router = OllamaRouter(config)

        headers = {
            "content-type": "application/json",
            "content-length": "100",
        }

        filtered = router._filter_headers(headers, for_response=True)

        assert "content-type" in filtered
        assert "content-length" not in filtered

    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        """Test that close method closes the HTTP client."""
        config = Config(ollama=OllamaConfig())
        router = OllamaRouter(config)

        router.client.aclose = AsyncMock()
        await router.close()

        router.client.aclose.assert_called_once()
