# Installation

## Prerequisites

- **Python 3.9+** (required)
- **llama-server binary** (required for local model serving)
  - Download from: https://github.com/ggerganov/llama.cpp/releases
  - Or install via package manager (e.g., `brew install llama-cpp`)
- **pip** (Python package manager)
- **Git**

## From Source

Clone the repository:

```bash
git clone https://github.com/Ananay28425/Sequence-LLM.git
cd Sequence-LLM
```

Install in development mode:

```bash
pip install -e .
```

Or install with all development dependencies for testing:

```bash
pip install -e ".[dev]"
```

## Virtual Environment (Recommended)

Create and activate a virtual environment:

```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install
pip install -e .
```

## Verify Installation

Check that the CLI is available:

```bash
seq-llm --help
```

You should see the Typer app help message.

## Runtime Dependencies

The package installs these automatically:

- `typer[all]>=0.7.0` — CLI framework (async/sync)
- `rich>=13.0.0` — Terminal styling and UI
- `httpx>=0.24.0` — HTTP client (sync mode, streaming)
- `psutil>=5.9.0` — Cross-platform process utilities
- `pyyaml>=6.0` — YAML configuration parsing
- `requests>=2.28.0` — HTTP library (health checks)

## llama-server Setup

1. **Download llama.cpp**:
   ```bash
   # via Homebrew (macOS)
   brew install llama-cpp

   # via release binary (all platforms)
   wget https://github.com/ggerganov/llama.cpp/releases/download/b<version>/llama-<platform>.zip
   unzip llama-<platform>.zip
   ```

2. **Verify installation**:
   ```bash
   llama-server --version
   ```

3. **Update config.yaml** with the path:
   ```yaml
   llama_server: "/usr/local/bin/llama-server"  # macOS/Linux
   # or
   llama_server: "C:\\path\\to\\llama-server.exe"  # Windows
   ```

## Troubleshooting

### Command not found: seq-llm

Ensure the Python Scripts directory is in your PATH:

```bash
# Verify installation
python -c "import seq_llm; print('OK')"

# Reinstall
pip install --force-reinstall -e .
```

### llama-server not found

Update `config.yaml` with the full path to the `llama-server` binary. See [Configuration](../docs/usage.md#configuration).

### Import errors

Test the package:

```bash
python -c "from seq_llm.config import Config; print('OK')"
```

### Health check fails on startup

- Ensure `llama-server` is installed and the path in `config.yaml` is correct
- Check that the model path is valid
- Try starting the server manually: `llama-server -m /path/to/model.gguf --port 8081`

