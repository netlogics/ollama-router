"""
Configuration module for ollama-router.
Manages SSL, server, Ollama connection, and logging settings.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from pathlib import Path


class SSLConfig(BaseModel):
    """SSL certificate configuration."""

    auto_generate: bool = Field(
        default=True, description="Auto-generate self-signed certificates"
    )
    cert_path: Optional[Path] = Field(
        default=None, description="Path to SSL certificate"
    )
    key_path: Optional[Path] = Field(
        default=None, description="Path to SSL private key"
    )
    cert_dir: Path = Field(
        default=Path(".certs"), description="Directory for certificates"
    )
    validity_days: int = Field(default=365, description="Certificate validity in days")


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8443, description="Server port")
    ssl: SSLConfig = Field(default_factory=SSLConfig)


class OllamaConfig(BaseModel):
    """Ollama connection configuration."""

    base_url: str = Field(
        default="http://localhost:11434", description="Ollama base URL"
    )
    timeout: int = Field(default=600, description="Default timeout in seconds")
    max_connections: int = Field(default=100, description="Max HTTP connections")


class RouteConfig(BaseModel):
    """Individual route configuration."""

    path: str = Field(description="Route path pattern")
    timeout: Optional[int] = Field(
        default=None, description="Route-specific timeout override"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format: json or text")
    log_requests: bool = Field(default=True, description="Log incoming requests")
    log_responses: bool = Field(
        default=False, description="Log responses (can be verbose)"
    )
    log_dir: Path = Field(default=Path("logs"), description="Log directory")


class Config(BaseSettings):
    """Main application configuration."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    routes: List[RouteConfig] = Field(default_factory=list)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_prefix = "OLLAMA_ROUTER_"
        env_nested_delimiter = "__"


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file or environment.

    Args:
        config_path: Optional path to YAML config file

    Returns:
        Config instance
    """
    if config_path and config_path.exists():
        import yaml

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        return Config(**data)
    return Config()


def get_default_config() -> Config:
    """Get default configuration with sensible defaults.

    Returns:
        Config with default route definitions
    """
    return Config(
        routes=[
            RouteConfig(path="/v1/chat/completions", timeout=600),
            RouteConfig(path="/v1/models", timeout=30),
            RouteConfig(path="/v1/embeddings", timeout=120),
            RouteConfig(path="/v1/completions", timeout=600),
        ]
    )
