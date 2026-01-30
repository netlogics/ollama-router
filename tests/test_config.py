"""
Test configuration for ollama-router.
"""

import pytest
from pathlib import Path
from src.config import (
    SSLConfig,
    ServerConfig,
    OllamaConfig,
    RouteConfig,
    LoggingConfig,
    Config,
    load_config,
    get_default_config,
)


class TestSSLConfig:
    """Tests for SSL configuration."""

    def test_default_ssl_config(self):
        """Test SSL config has sensible defaults."""
        config = SSLConfig()
        assert config.auto_generate is True
        assert config.cert_path is None
        assert config.key_path is None
        assert config.cert_dir == Path(".certs")
        assert config.validity_days == 365

    def test_custom_ssl_config(self):
        """Test SSL config accepts custom values."""
        config = SSLConfig(
            auto_generate=False,
            cert_path=Path("/custom/cert.pem"),
            key_path=Path("/custom/key.pem"),
            cert_dir=Path("/custom/certs"),
            validity_days=730,
        )
        assert config.auto_generate is False
        assert config.cert_path == Path("/custom/cert.pem")
        assert config.key_path == Path("/custom/key.pem")
        assert config.cert_dir == Path("/custom/certs")
        assert config.validity_days == 730


class TestServerConfig:
    """Tests for server configuration."""

    def test_default_server_config(self):
        """Test server config has sensible defaults."""
        config = ServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8443
        assert isinstance(config.ssl, SSLConfig)


class TestOllamaConfig:
    """Tests for Ollama connection configuration."""

    def test_default_ollama_config(self):
        """Test Ollama config has sensible defaults."""
        config = OllamaConfig()
        assert config.base_url == "http://localhost:11434"
        assert config.timeout == 600
        assert config.max_connections == 100


class TestRouteConfig:
    """Tests for route configuration."""

    def test_route_config_with_timeout(self):
        """Test route config with custom timeout."""
        config = RouteConfig(path="/v1/chat/completions", timeout=600)
        assert config.path == "/v1/chat/completions"
        assert config.timeout == 600

    def test_route_config_without_timeout(self):
        """Test route config without timeout (uses default)."""
        config = RouteConfig(path="/v1/models")
        assert config.path == "/v1/models"
        assert config.timeout is None


class TestLoggingConfig:
    """Tests for logging configuration."""

    def test_default_logging_config(self):
        """Test logging config has sensible defaults."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.log_requests is True
        assert config.log_responses is False
        assert config.log_dir == Path("logs")


class TestConfig:
    """Tests for main application configuration."""

    def test_default_config(self):
        """Test main config has all required sections."""
        config = Config()
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.ollama, OllamaConfig)
        assert isinstance(config.routes, list)
        assert isinstance(config.logging, LoggingConfig)

    def test_get_default_config(self):
        """Test get_default_config returns config with routes."""
        config = get_default_config()
        assert isinstance(config, Config)
        assert len(config.routes) == 4
        # Check route paths
        paths = [r.path for r in config.routes]
        assert "/v1/chat/completions" in paths
        assert "/v1/models" in paths
        assert "/v1/embeddings" in paths
        assert "/v1/completions" in paths
