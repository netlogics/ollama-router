"""
Request logging middleware for ollama-router.
Provides structured JSON logging of requests and responses.
"""

import json
import time
import logging
from pathlib import Path
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.config import LoggingConfig


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "model"):
            log_data["model"] = record.model

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""

    def __init__(self, app, config: LoggingConfig):
        super().__init__(app)
        self.config = config
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with appropriate formatter."""
        logger = logging.getLogger("ollama_router")
        logger.setLevel(getattr(logging, self.config.level.upper()))

        # Ensure log directory exists
        self.config.log_dir.mkdir(parents=True, exist_ok=True)

        # File handler
        log_file = self.config.log_dir / "router.log"
        file_handler = logging.FileHandler(log_file)

        # Console handler
        console_handler = logging.StreamHandler()

        # Set formatter
        if self.config.format == "json":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    async def dispatch(self, request: Request, call_next):
        """Process request and log details."""
        if not self.config.log_requests:
            return await call_next(request)

        start_time = time.time()

        # Extract model from request body if possible
        model = None
        try:
            body = await request.body()
            if body:
                data = json.loads(body)
                model = data.get("model")

                # Reset body for next middleware/handler
                async def receive():
                    return {"type": "http.request", "body": body}

                request._receive = receive
        except Exception:
            pass

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Create log record with extra fields
        extra = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        if model:
            extra["model"] = model

        # Log request
        self.logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
            extra=extra,
        )

        return response


def get_logger(name: str = "ollama_router") -> logging.Logger:
    """Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
