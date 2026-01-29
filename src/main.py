"""
Main FastAPI application for ollama-router.
"""

import argparse
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from src.config import load_config, get_default_config, Config
from src.ssl_manager import SSLManager
from src.router import OllamaRouter
from src.logging import RequestLoggingMiddleware, get_logger

# Global state
config: Config = None
router: OllamaRouter = None
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global config, router

    # Startup
    logger.info("Starting ollama-router...")

    # Ensure SSL certificates
    ssl_manager = SSLManager(config.server.ssl)
    cert_path, key_path = ssl_manager.ensure_certificates()
    logger.info(f"SSL certificates ready: {cert_path}")

    # Initialize router
    router = OllamaRouter(config)
    logger.info(f"Router initialized with Ollama at {config.ollama.base_url}")

    yield

    # Shutdown
    logger.info("Shutting down ollama-router...")
    if router:
        await router.close()


def create_app(config_path: Path = None) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        config_path: Optional path to config file

    Returns:
        Configured FastAPI app
    """
    global config

    # Load configuration
    if config_path:
        config = load_config(config_path)
    else:
        config = get_default_config()

    # Create app
    app = FastAPI(
        title="Ollama Router",
        description="HTTPS proxy for Ollama with configurable timeouts",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add logging middleware
    app.add_middleware(RequestLoggingMiddleware, config=config.logging)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    # Proxy all Ollama API endpoints
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def proxy(path: str, request: Request):
        """Proxy all requests to Ollama."""
        # Skip health check
        if path == "health":
            return await health_check()

        # Read request body
        body = await request.body()

        # Check if streaming is requested
        is_streaming = False
        if body:
            try:
                import json

                data = json.loads(body)
                is_streaming = data.get("stream", False)
            except Exception:
                pass

        # Route to appropriate handler
        if is_streaming:
            return await router.proxy_streaming_request(request, f"/{path}", body)
        else:
            return await router.proxy_request(request, f"/{path}", body)

    return app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ollama Router - HTTPS proxy for Ollama"
    )
    parser.add_argument("--config", type=Path, help="Path to configuration file (YAML)")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Server bind address (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8443, help="Server port (default: 8443)"
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama base URL (default: http://localhost:11434)",
    )

    args = parser.parse_args()

    # Create app
    app = create_app(args.config)

    # Update config from CLI args if provided
    if args.host:
        config.server.host = args.host
    if args.port:
        config.server.port = args.port
    if args.ollama_url:
        config.ollama.base_url = args.ollama_url

    # Ensure SSL certificates
    ssl_manager = SSLManager(config.server.ssl)
    cert_path, key_path = ssl_manager.ensure_certificates()

    # Start server
    import uvicorn

    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        ssl_keyfile=str(key_path),
        ssl_certfile=str(cert_path),
        log_level="info",
    )


if __name__ == "__main__":
    main()
