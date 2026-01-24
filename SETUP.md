# Setup Instructions

## Quick Start with mise

1. Install mise (if not already installed):
   ```bash
   curl https://mise.run | sh
   ```

2. Install Python and uv via mise:
   ```bash
   mise use -g python@latest uv@latest
   ```

3. Install dependencies:
   ```bash
   mise run install
   ```
   Or manually:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

4. Run the chat application:
   ```bash
   python chat.py --model <your-model-path>
   ```

## Example

```bash
# One-time setup
mise use -g python@latest uv@latest
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run with a model
python chat.py --model nemotron-3-nano:latest
```

## Notes

- `mise` manages Python and uv versions automatically
- `uv` is significantly faster than pip for installing packages
- The virtual environment will be created in `.venv/` directory
- Make sure you have sufficient disk space for model downloads
