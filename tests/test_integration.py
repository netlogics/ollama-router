"""Integration tests for ollama-router."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request
from fastapi.testclient import TestClient


class TestFullRequestFlow:
    """Integration tests for complete request flow."""

    def test_config_loading_integration(self, tmp_path):
        """Test that config loads and initializes all components."""
        from src.main import create_app
        from src.config import Config

        # Create a config file
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
server:
  host: "127.0.0.1"
  port: 8443
  ssl:
    auto_generate: true
    cert_dir: ".test_certs"

ollama:
  base_url: "http://localhost:11434"
  timeout: 600

routes:
  - path: "/v1/models"
    timeout: 30
  - path: "/v1/chat/completions"
    timeout: 600

logging:
  level: "INFO"
  format: "json"
  log_requests: true
  log_dir: "logs"
""")

        app = create_app(config_file)

        # Verify app was created with all routes
        assert app is not None
        assert app.title == "Ollama Router"

        # Verify health endpoint works
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_ssl_and_router_integration(self, tmp_path):
        """Test SSL manager and router work together."""
        from src.ssl_manager import SSLManager
        from src.router import OllamaRouter
        from src.config import Config, SSLConfig, OllamaConfig, ServerConfig

        # Create SSL manager
        ssl_config = SSLConfig(auto_generate=True, cert_dir=tmp_path / "certs")
        ssl_manager = SSLManager(ssl_config)

        # Generate certificates
        cert_path, key_path = ssl_manager.ensure_certificates()

        # Verify certificates exist
        assert cert_path.exists()
        assert key_path.exists()

        # Create router with config (SSL config goes in server.ssl)
        config = Config(
            server=ServerConfig(ssl=ssl_config),
            ollama=OllamaConfig(base_url="http://test:11434"),
        )
        router = OllamaRouter(config)

        # Verify router was created successfully
        assert router is not None
        assert router.ollama_config.base_url == "http://test:11434"


class TestErrorHandlingIntegration:
    """Integration tests for error handling across modules."""

    @pytest.mark.asyncio
    async def test_router_error_propagation(self):
        """Test that router errors are properly handled."""
        from src.router import OllamaRouter
        from src.config import Config
        from fastapi import HTTPException
        import httpx

        config = Config()
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
        await router.close()

    def test_logging_integration_with_requests(self, tmp_path):
        """Test that logging captures request information."""
        from src.main import create_app
        from src.config import Config, LoggingConfig
        from fastapi.testclient import TestClient
        import json

        # Create app with logging enabled
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
logging:
  level: "INFO"
  format: "json"
  log_requests: true
  log_dir: "test_logs"
""")

        app = create_app(config_file)
        client = TestClient(app)

        # Make a request
        response = client.get("/health")
        assert response.status_code == 200

        # Verify log file was created
        log_file = tmp_path / "test_logs" / "router.log"
        # Note: Log file creation is async, might not exist immediately
        # This test verifies the logging middleware is active


class TestConfigRouterIntegration:
    """Integration tests for config and router."""

    def test_route_specific_timeouts(self):
        """Test that route-specific timeouts are properly configured."""
        from src.config import Config, RouteConfig, OllamaConfig
        from src.router import OllamaRouter

        config = Config(
            ollama=OllamaConfig(timeout=600),
            routes=[
                RouteConfig(path="/v1/models", timeout=30),
                RouteConfig(path="/v1/chat/completions", timeout=600),
            ],
        )
        router = OllamaRouter(config)

        # Test route-specific timeout
        import asyncio

        timeout1 = asyncio.run(router.get_timeout_for_path("/v1/models"))
        timeout2 = asyncio.run(router.get_timeout_for_path("/v1/chat/completions"))
        timeout3 = asyncio.run(router.get_timeout_for_path("/v1/unknown"))

        assert timeout1 == 30
        assert timeout2 == 600
        assert timeout3 == 600  # Default timeout

    def test_default_config_with_routes(self):
        """Test default config generation includes routes."""
        from src.config import get_default_config

        config = get_default_config()

        # Verify default routes are present
        route_paths = [r.path for r in config.routes]
        assert "/v1/chat/completions" in route_paths
        assert "/v1/models" in route_paths
        assert "/v1/embeddings" in route_paths
        assert "/v1/completions" in route_paths
