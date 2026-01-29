"""
Request router and proxy for Ollama.
Handles request forwarding with configurable timeouts and streaming support.
"""

import json
import time
from typing import Optional
import httpx
from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from src.config import Config, OllamaConfig


class OllamaRouter:
    """Routes requests to Ollama with timeout and streaming support."""

    def __init__(self, config: Config):
        self.config = config
        self.ollama_config = config.ollama

        # Create async HTTP client with connection pooling
        limits = httpx.Limits(
            max_connections=self.ollama_config.max_connections,
            max_keepalive_connections=20,
        )
        timeout = httpx.Timeout(
            connect=10.0, read=float(self.ollama_config.timeout), write=10.0, pool=10.0
        )
        self.client = httpx.AsyncClient(
            base_url=self.ollama_config.base_url, limits=limits, timeout=timeout
        )

    async def get_timeout_for_path(self, path: str) -> float:
        """Get timeout for a specific path.

        Args:
            path: Request path

        Returns:
            Timeout in seconds
        """
        # Check for route-specific timeout
        for route in self.config.routes:
            if path.startswith(route.path):
                if route.timeout is not None:
                    return float(route.timeout)

        # Default timeout
        return float(self.ollama_config.timeout)

    async def proxy_request(
        self, request: Request, path: str, body: Optional[bytes] = None
    ) -> Response:
        """Proxy a request to Ollama.

        Args:
            request: Incoming FastAPI request
            path: Path to forward to
            body: Request body (if already read)

        Returns:
            Response from Ollama
        """
        # Get timeout for this path
        timeout = await self.get_timeout_for_path(path)

        # Build headers (filter out hop-by-hop headers)
        headers = self._filter_headers(dict(request.headers))

        # Read body if not provided
        if body is None:
            body = await request.body()

        try:
            # Forward request to Ollama
            response = await self.client.request(
                method=request.method,
                url=path,
                headers=headers,
                content=body,
                timeout=timeout,
            )

            # Build response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=504,
                detail=f"Ollama request timed out after {timeout}s: {str(e)}",
            )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=502, detail=f"Could not connect to Ollama: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error proxying request: {str(e)}"
            )

    async def proxy_streaming_request(
        self, request: Request, path: str, body: Optional[bytes] = None
    ) -> StreamingResponse:
        """Proxy a streaming request (Server-Sent Events) to Ollama.

        Args:
            request: Incoming FastAPI request
            path: Path to forward to
            body: Request body (if already read)

        Returns:
            StreamingResponse
        """
        timeout = await self.get_timeout_for_path(path)

        headers = self._filter_headers(dict(request.headers))

        if body is None:
            body = await request.body()

        try:
            # Make streaming request
            async def stream_generator():
                async with self.client.stream(
                    method=request.method,
                    url=path,
                    headers=headers,
                    content=body,
                    timeout=timeout,
                ) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk

            # Make initial request to get headers
            response = await self.client.request(
                method=request.method,
                url=path,
                headers=headers,
                content=body,
                timeout=timeout,
            )

            return StreamingResponse(
                stream_generator(),
                status_code=response.status_code,
                headers=self._filter_headers(dict(response.headers), for_response=True),
            )

        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=504,
                detail=f"Ollama streaming request timed out after {timeout}s",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error proxying streaming request: {str(e)}"
            )

    def _filter_headers(self, headers: dict, for_response: bool = False) -> dict:
        """Filter hop-by-hop headers.

        Args:
            headers: Headers to filter
            for_response: If True, filter for response headers

        Returns:
            Filtered headers
        """
        hop_by_hop = {
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
        }

        filtered = {}
        for key, value in headers.items():
            if key.lower() not in hop_by_hop:
                if for_response and key.lower() == "content-length":
                    # Skip content-length for streaming responses
                    continue
                filtered[key] = value

        return filtered

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
