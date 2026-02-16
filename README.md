# Sequence-LLM

A terminal-first CLI for managing local LLMs running via `llama-server`. Ensures **STRICT SEQUENTIAL LOADING** — only one model at a time. Cross-platform (Windows/Linux/macOS).

## Overview

Sequence-LLM provides:

- **Interactive CLI** (Typer + Rich): commands to switch between profiles, chat, and view status
- **Single-process management**: Only one `llama-server` running at a time; new profile switch stops the old one
- **Profile-based config**: Organize models into named profiles (e.g., `brain`, `coder`)
- **Auto-start on launch**: Attempts to start the default profile (`brain`) on CLI boot
- **Health polling**: Waits for server readiness via `/health` endpoint (1s intervals, 30s timeout)
- **Cross-platform**: Works on Windows, Linux, and macOS using `subprocess` + `psutil`

## Features

- 🧠 **Profile switching**: `/brain`, `/coder`, etc. — seamless model swaps
- 💬 **Interactive chat loop**: Send messages (just type, no prefix), get prefixed replies
- 🔄 **Graceful shutdown**: SIGTERM → SIGKILL on profile switch or `/quit`
- ⚙️ **OS-aware config paths**: Auto-creates config in the right place per OS
- 🛡️ **Safe port handling**: Kills only matching `llama-server` processes when port is in use
- 📊 **Status panel**: `/status` displays active model, port, PID, uptime (Rich Panel)

## Installation

### Requirements

- Python 3.9+
- `llama-server` binary in PATH or configured in `config.yaml`

### From source

```bash
git clone https://github.com/Ananay28425/Sequence-LLM.git
cd Sequence-LLM
pip install -e .
```

This installs the `seq-llm` command.

## Quick Start

### 1. Launch the CLI

```bash
pip install sequence-llm
seq-llm
```

On first run, a default config is created at:
- **Windows**: `%APPDATA%\sequence-llm\config.yaml`
- **Linux**: `~/.config/sequence-llm/config.yaml`
- **macOS**: `~/Library/Application Support/sequence-llm/config.yaml`

The CLI auto-attempts to start the `brain` profile. If it fails, you'll see a warning.

### 2. Edit the config file

Update the paths to your `llama-server` binary and model files:

```yaml
llama_server: "/opt/llama-server/llama-server"

defaults:
  threads: 6
  threads_batch: 8
  batch_size: 512

profiles:
  brain:
    name: "Brain (GLM-4.7-Flash)"
    model_path: "/path/to/model.gguf"
    system_prompt: "/path/to/system.txt"
    port: 8081
    ctx_size: 16384
    temperature: 0.7

  coder:
    name: "Coder (Qwen2.5-Coder-7B)"
    model_path: "/path/to/coder.gguf"
    system_prompt: "/path/to/coder_system.txt"
    port: 8082
    ctx_size: 32768
    temperature: 0.3
```

### 3. Use the CLI

```
You> /status
  → Shows active model, port, health status

You> /brain
  → Switches to brain profile (stops current server, starts brain)

You> /coder
  → Switches to coder profile

You> Hello, how are you?
  → Sends message to active model (prefixed reply: "Brain> ...")

You> /clear
  → Clears conversation history (does NOT stop server)

You> /quit
  → Stops server and exits CLI
```

## Configuration

See [docs/installation.md](docs/installation.md) and [docs/usage.md](docs/usage.md) for detailed guides.

### Config Schema

```yaml
llama_server: "<path to llama-server binary>"

defaults:             # Default args passed to all llama-server invocations
  threads: 6
  threads_batch: 8
  batch_size: 512

profiles:             # Named model profiles
  <profile_name>:
    name: "<human-readable name>"
    model_path: "<path to .gguf or model file>"
    system_prompt: "<path to system prompt file>"
    port: <port number>
    ctx_size: <context size>
    temperature: <float 0.0-2.0>
```

### Full Config Example

See [tests/fixtures/sample_config.yaml](tests/fixtures/sample_config.yaml).

## Project Structure

```
sequence-llm/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── index.md
│   ├── installation.md
│   └── usage.md
├── examples/
│   └── basic_workflow.md
├── src/seq_llm/
│   ├── __init__.py
│   ├── cli.py                 # Interactive CLI (Typer + Rich)
│   ├── config.py              # Config loading/validation (dataclasses + YAML)
│   └── core/
│       ├── __init__.py
│       ├── server_manager.py  # llama-server lifecycle (subprocess + psutil)
│       └── api_client.py      # Chat completions API (httpx streaming)
├── tests/
│   ├── fixtures/
│   │   └── sample_config.yaml
│   └── unit/
│       ├── test_config.py
│       └── test_server_manager.py
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Tech Stack

- **CLI**: Typer + Rich (interactive, styled terminal UI)
- **Config**: `dataclasses` + `pyyaml` (simple, no Pydantic)
- **Process management**: `subprocess` + `psutil` (cross-platform)
- **HTTP client**: `httpx` (sync mode, streaming support)
- **Tests**: `pytest` (unit tests with mocks)

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [API Reference](docs/index.md)
- [Example Workflow](examples/basic_workflow.md)

## License

MIT — see [LICENSE](LICENSE)


## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Troubleshooting

### Server won't start

- Check if port is already in use: `lsof -i :11434` (macOS/Linux)
- Ensure Ollama/LM Studio is installed
- Check server type configuration matches installed software

### API connection errors

- Verify server is running: `curl http://localhost:11434/api/status`
- Check host and port in configuration
- Ensure model is available on the server

### Model not found

- List available models: `ollama list` (for Ollama)
- Pull model before running: `ollama pull llama2`
- Update configuration with correct model name

## Support

For issues, questions, or suggestions, please open an issue on [GitHub](https://github.com/yourusername/Sequence-LLM/issues).

---

**Sequence-LLM** - Orchestrate LLM sequences with ease.
