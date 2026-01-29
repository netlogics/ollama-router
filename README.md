# Ollama Router

HTTPS proxy for Ollama with configurable timeouts, designed to solve connection timeout issues when using large language models (30B+ parameters) with tools like OpenCode.

## Features

- **HTTPS Support** - Auto-generated self-signed SSL certificates
- **Long Timeouts** - Configurable 10+ minute timeouts for large models
- **Streaming Support** - Full Server-Sent Events (SSE) streaming for chat completions
- **Request Logging** - Structured JSON logging of all requests
- **Zero Configuration** - Works out of the box with sensible defaults

## Quick Start

### Prerequisites

- Python 3.8+
- Ollama installed and running locally

### Installation

```bash
# Clone or navigate to the project
cd ~/dev/ollama-router

# Install dependencies
pip install -r requirements.txt

# Start the router
python -m src.main
```

The router will:
1. Generate self-signed SSL certificates in `.certs/`
2. Start HTTPS server on port 8443
3. Proxy requests to Ollama at http://localhost:11434

### Usage

Point your OpenAI-compatible client to:
```
https://localhost:8443/v1
```

Example with curl:
```bash
curl -k -X POST https://localhost:8443/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-coder:30b-32k",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

Note: Use `-k` flag to skip SSL verification (self-signed cert).

## Configuration

Create a `config.yaml` file (or use the provided default):

```yaml
server:
  host: "0.0.0.0"
  port: 8443
  ssl:
    auto_generate: true
    cert_dir: ".certs"
    validity_days: 365

ollama:
  base_url: "http://localhost:11434"
  timeout: 600  # 10 minutes for large models

routes:
  - path: "/v1/chat/completions"
    timeout: 600  # Long timeout for chat
  - path: "/v1/models"
    timeout: 30   # Short timeout for model list

logging:
  level: "INFO"
  format: "json"
  log_requests: true
  log_dir: "logs"
```

### Command Line Options

```bash
python -m src.main --help

# Custom config file
python -m src.main --config myconfig.yaml

# Custom Ollama URL
python -m src.main --ollama-url http://192.168.1.100:11434

# Custom port
python -m src.main --port 9443
```

## Environment Variables

All configuration options can be set via environment variables:

```bash
export OLLAMA_ROUTER_SERVER__PORT=9443
export OLLAMA_ROUTER_OLLAMA__TIMEOUT=900
export OLLAMA_ROUTER_LOGGING__LEVEL=DEBUG
```

## Architecture

```
┌─────────────────┐     HTTPS      ┌──────────────────┐     HTTP      ┌─────────────┐
│   OpenCode      │ ───────────────> │  ollama-router   │ ────────────> │   Ollama    │
│   (or other     │    Port 8443    │   (this proxy)   │   Port 11434  │             │
│    client)      │                  │                  │               │             │
└─────────────────┘                  └──────────────────┘               └─────────────┘
```

## Troubleshooting

### SSL Certificate Issues

The router auto-generates self-signed certificates. To trust them:

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain .certs/server.crt
```

**Linux:**
```bash
sudo cp .certs/server.crt /usr/local/share/ca-certificates/ollama-router.crt
sudo update-ca-certificates
```

### Timeout Issues

If you're still experiencing timeouts:

1. Check Ollama logs: `ollama serve 2>&1 | grep -i timeout`
2. Increase timeout in config: `timeout: 900` (15 minutes)
3. Verify Ollama can handle the model: `ollama run qwen3-coder:30b-32k`

### Connection Refused

Ensure Ollama is running:
```bash
ollama serve
```

Or check if Ollama is on a different host/port.

## Development

### Project Structure

```
ollama-router/
├── src/
│   ├── __init__.py
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # Configuration management
│   ├── router.py         # HTTP proxy logic
│   ├── ssl_manager.py    # Certificate generation
│   └── logging.py        # Request logging
├── tests/                # Test suite
├── config.yaml           # Default configuration
├── requirements.txt      # Dependencies
└── README.md            # This file
```

### Running Tests

```bash
pytest tests/
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please submit issues and pull requests.

## Acknowledgments

Built to solve timeout issues when using OpenCode with large local models via Ollama.
