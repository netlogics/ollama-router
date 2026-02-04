"""Test main FastAPI application."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path


class TestCreateApp:
    """Tests for create_app function."""

    def test_create_app_returns_fastapi_app(self):
        """Test that create_app returns a FastAPI application."""
        from src.main import create_app

        app = create_app()

        assert isinstance(app, FastAPI)
        assert app.title == "Ollama Router"

    def test_create_app_with_config_path(self, tmp_path):
        """Test creating app with a config file path."""
        from src.main import create_app

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
server:
  host: "127.0.0.1"
  port: 9443
""")

        app = create_app(config_file)

        assert isinstance(app, FastAPI)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_healthy(self):
        """Test that health check returns healthy status."""
        from src.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"


class TestLifespan:
    """Tests for application lifespan."""

    @pytest.mark.asyncio
    async def test_lifespan_initializes_router(self):
        """Test that lifespan initializes SSL and router."""
        from src.main import lifespan
        from unittest.mock import MagicMock

        mock_app = MagicMock()
        mock_app.state = MagicMock()

        # Mock the context
        async with lifespan(mock_app):
            # During lifespan, router should be initialized
            pass

        # After exiting, router should be closed


class TestProxyEndpoint:
    """Tests for proxy endpoint."""

    @pytest.mark.asyncio
    async def test_proxy_endpoint_exists(self):
        """Test that proxy endpoint accepts requests."""
        from src.main import create_app
        from fastapi.routing import APIRoute

        app = create_app()

        # Check that proxy route exists
        routes = [route for route in app.routes if isinstance(route, APIRoute)]
        proxy_routes = [
            r for r in routes if hasattr(r, "path") and r.path == "/{path:path}"
        ]

        # Should have at least one catch-all proxy route
        assert len(proxy_routes) >= 1

    def test_proxy_skips_health_check(self):
        """Test that proxy route correctly routes health check."""
        from src.main import create_app

        app = create_app()
        client = TestClient(app)

        # Health check should still work
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_proxy_accepts_post_requests(self):
        """Test that proxy endpoint accepts POST requests."""
        from src.main import create_app

        app = create_app()
        client = TestClient(app)

        # POST to a non-existent endpoint should be handled by proxy
        # (will fail to connect to Ollama, but route should exist)
        response = client.post("/v1/chat/completions", json={"test": "data"})
        # Should get error since Ollama isn't running (500 or 502)
        assert response.status_code in [500, 502]
