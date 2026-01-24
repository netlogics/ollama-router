# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Repository Overview

This is an Ollama-based local chat application built in Python. It provides a command-line interface for interacting with large language models running locally using Ollama.

## Project Structure

```
airllm-local-chat/
├── chat.py              # Main chat application entry point
├── src/                 # Source package directory
│   └── __init__.py
├── requirements.txt     # Python dependencies
├── README.md           # User documentation
└── SETUP.md            # Setup instructions using mise
```

## Development Commands

### Setup
```bash
# Using mise and uv
mise use -g python@latest uv@latest
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Running
```bash
# Ensure Ollama is running
ollama serve

# Run with default model (nemotron-3-nano:latest)
python chat.py

# Or specify a model
python chat.py --model llama2:latest
```

## Architecture

- **chat.py**: Main application with ChatBot class
  - Connects to Ollama server for inference
  - Manages conversation history
  - Provides interactive CLI using Rich library
  - Supports commands: quit/exit/q, clear
  - Default model: nemotron-3-nano:latest

## Dependencies

- **ollama**: Ollama Python client for LLM inference
- **rich**: Terminal formatting and UI
- **python-dotenv**: Environment variable management
