# Ollama Local Chat

A simple command-line chat interface for running large language models locally using Ollama.

## Features

- Interactive chat interface with conversation history
- Support for any Ollama model
- Rich terminal UI with formatting
- Simple commands for managing conversations

## Installation

1. Install Ollama from https://ollama.ai
2. Pull a model:
   ```bash
   ollama pull nemotron-3-nano:latest
   ```

3. Clone the repository and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

## Usage

Make sure Ollama is running:
```bash
ollama serve
```

Run the chat application (uses nemotron-3-nano:latest by default):

```bash
python chat.py
```

Or specify a different model:
```bash
python chat.py --model llama2:latest
```

### Chat Commands

- `quit`, `exit`, or `q` - Exit the chat
- `clear` - Clear conversation history
- `Ctrl+C` - Exit the chat

## Requirements

- Python 3.8+
- Ollama installed and running
- At least one Ollama model pulled locally

## License

MIT
