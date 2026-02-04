"""Test logging module."""

import json
import logging
import pytest


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_basic_format(self):
        """Test basic log formatting."""
        from src.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        from src.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Request logged",
            args=(),
            exc_info=None,
        )
        # Add extra fields
        record.request_id = "12345"
        record.method = "POST"
        record.path = "/v1/chat/completions"
        record.status_code = 200
        record.duration_ms = 150.5
        record.model = "test-model"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["request_id"] == "12345"
        assert data["method"] == "POST"
        assert data["status_code"] == 200

    def test_format_with_exception(self):
        """Test formatting when exception info is present."""
        from src.logging import JSONFormatter

        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "ERROR"
        assert "exception" in data


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        from src.logging import get_logger

        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "ollama_router"

    def test_get_logger_with_custom_name(self):
        """Test get_logger with custom name."""
        from src.logging import get_logger

        logger = get_logger("custom_logger")
        assert logger.name == "custom_logger"


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware."""

    def test_setup_logger_creates_handlers(self, tmp_path):
        """Test that _setup_logger creates file and console handlers."""
        from unittest.mock import Mock
        from src.logging import RequestLoggingMiddleware
        from src.config import LoggingConfig

        config = LoggingConfig(log_dir=tmp_path, format="json")
        mock_app = Mock()
        middleware = RequestLoggingMiddleware(mock_app, config)

        assert middleware.logger is not None
        assert len(middleware.logger.handlers) == 2
        log_file = tmp_path / "router.log"
        assert log_file.exists()

    @pytest.mark.asyncio
    async def test_dispatch_skips_logging_when_disabled(self, tmp_path):
        """Test that dispatch skips logging when log_requests is False."""
        from unittest.mock import Mock, AsyncMock
        from src.logging import RequestLoggingMiddleware
        from src.config import LoggingConfig
        from fastapi import Request

        config = LoggingConfig(log_dir=tmp_path, log_requests=False)
        mock_app = Mock()
        middleware = RequestLoggingMiddleware(mock_app, config)

        request = Mock(spec=Request)
        request.body = AsyncMock(return_value=b"test")
        mock_response = Mock()

        async def mock_call_next(request):
            return mock_response

        response = await middleware.dispatch(request, mock_call_next)
        assert response == mock_response
        request.body.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_logs_request_with_model(self, tmp_path):
        """Test that dispatch logs request with model info."""
        from unittest.mock import Mock, AsyncMock
        from src.logging import RequestLoggingMiddleware
        from src.config import LoggingConfig
        from fastapi import Request

        config = LoggingConfig(log_dir=tmp_path, log_requests=True, format="json")
        mock_app = Mock()
        middleware = RequestLoggingMiddleware(mock_app, config)

        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/v1/chat/completions"
        body_content = b'{"model": "test-model"}'
        request.body = AsyncMock(return_value=body_content)

        mock_response = Mock()
        mock_response.status_code = 200

        async def mock_call_next(request):
            return mock_response

        response = await middleware.dispatch(request, mock_call_next)
        assert response == mock_response

        log_file = tmp_path / "router.log"
        assert log_file.exists()

    @pytest.mark.asyncio
    async def test_dispatch_handles_invalid_json(self, tmp_path):
        """Test that dispatch handles invalid JSON gracefully."""
        from unittest.mock import Mock, AsyncMock
        from src.logging import RequestLoggingMiddleware
        from src.config import LoggingConfig
        from fastapi import Request

        config = LoggingConfig(log_dir=tmp_path, log_requests=True)
        mock_app = Mock()
        middleware = RequestLoggingMiddleware(mock_app, config)

        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/v1/chat/completions"
        request.body = AsyncMock(return_value=b"not valid json")

        mock_response = Mock()
        mock_response.status_code = 200

        async def mock_call_next(request):
            return mock_response

        response = await middleware.dispatch(request, mock_call_next)
        assert response == mock_response
        log_file = tmp_path / "router.log"
        assert log_file.exists()
