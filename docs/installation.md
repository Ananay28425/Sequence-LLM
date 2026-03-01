# Installation

## Prerequisites

- Python 3.9 or newer
- `llama-server` binary (required for local model serving)
  - Download from: https://github.com/ggerganov/llama.cpp/releases
  - Or install via package manager when available
- pip
- Git

## From Source

```bash
pip install sequence-llm
```

## For Developers and Contributors

Clone the repository:

```bash
git clone https://github.com/Ananay28425/Sequence-LLM.git
cd Sequence-LLM
```

Install in development mode:

```bash
pip install -e .
```

Or install with development dependencies for testing:

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

You should see the Typer app help output.

## Runtime Dependencies

The package depends on:

- typer[all] >= 0.7.0
- rich >= 13.0.0
- httpx >= 0.24.0
- psutil >= 5.9.0
- pyyaml >= 6.0
- requests >= 2.28.0

These are installed automatically by pip.

## llama-server Setup

1. Download or build llama.cpp and the `llama-server` binary.

2. Verify installation by running:

```bash
llama-server --version
```

3. Update your `config.yaml` with the full path to `llama-server`:

```yaml
llama_server: "/usr/local/bin/llama-server"  # macOS/Linux
# or
llama_server: "C:\\path\\to\\llama-server.exe"  # Windows
```

## Troubleshooting

### Command not found: seq-llm

Ensure the Python Scripts directory is in your PATH and that the editable install succeeded:

```bash
python -c "import seq_llm; print('OK')"
pip install --force-reinstall -e .
```

### llama-server not found

Update `config.yaml` with the full path to the `llama-server` binary.

### Health check fails on startup

- Verify `llama-server` exists and is executable
- Verify the model file path
- Check port availability on the configured port
- Try starting `llama-server` manually with the model to see detailed errors
