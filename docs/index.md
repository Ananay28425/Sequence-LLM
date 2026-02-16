# Sequence-LLM Documentation

A terminal-first CLI for managing local LLMs via `llama-server`. Ensures **only one model runs at a time** with seamless profile switching.

## Table of Contents

- [Installation](./installation.md) — Setup and dependencies
- [Usage](./usage.md) — Interactive CLI, configuration, and commands
- [Examples](../examples/basic_workflow.md) — Sample workflows and patterns

## Quick Start

```bash
# 1. Install
pip install -e .

# 2. Launch interactive CLI
seq-llm

# 3. On first run, a config is created at:
#    - Windows: %APPDATA%\sequence-llm\config.yaml
#    - Linux:   ~/.config/sequence-llm/config.yaml
#    - macOS:   ~/Library/Application Support/sequence-llm/config.yaml

# 4. Edit the config to point to your llama-server and models

# 5. Use commands:
#    /brain    — switch to brain profile
#    /coder    — switch to coder profile
#    /status   — show active model status
#    /clear    — clear conversation history
#    /quit     — stop server and exit
#    (text)    — send chat message to active model
```

## Key Features

- 🧠 **Profile-based profiles**: Define named profiles (brain, coder, etc.) in YAML
- 💬 **Interactive CLI**: Typer + Rich for beautiful terminal UI
- 🔄 **Sequential loading**: Only one `llama-server` at a time; switching kills the old one
- ⚙️ **Auto-config**: Creates sensible defaults on first run
- 📊 **Status panel**: Rich-formatted output showing active model, port, health
- 🛡️ **Safe shutdown**: Graceful SIGTERM → SIGKILL on profile switch or exit
- 🔌 **Cross-platform**: Windows, Linux, macOS (uses `subprocess` + `psutil`)

## Architecture

Three core modules:

1. **Config** (`config.py`) — Load/validate YAML profiles, OS-aware config paths
2. **ServerManager** (`core/server_manager.py`) — Start/stop `llama-server`, health polling
3. **APIClient** (`core/api_client.py`) — Stream chat completions via `httpx`
4. **CLI** (`cli.py`) — Typer + Rich interactive loop

## Configuration Schema

```yaml
llama_server: "/path/to/llama-server"

defaults:
  threads: 6
  threads_batch: 8
  batch_size: 512

profiles:
  profile_name:
    name: "Display Name"
    model_path: "/path/to/model.gguf"
    system_prompt: "/path/to/system.txt"
    port: 8081
    ctx_size: 16384
    temperature: 0.7
```

See [Usage](./usage.md) for full reference.

## Tech Stack

- **CLI**: Typer + Rich (modern async/sync, beautiful UI)
- **Config**: dataclasses + pyyaml (simple, no Pydantic)
- **Process**: subprocess + psutil (cross-platform)
- **HTTP**: httpx (sync mode, streaming)
- **Tests**: pytest (unit tests with mocks)

## File Structure

```
sequence-llm/
├── src/seq_llm/
│   ├── cli.py              # Interactive CLI entry point
│   ├── config.py           # YAML config + dataclasses
│   └── core/
│       ├── server_manager.py    # Process lifecycle
│       └── api_client.py        # Chat API streaming
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   └── test_server_manager.py
│   └── fixtures/
│       └── sample_config.yaml
├── docs/
│   ├── index.md            # This file
│   ├── installation.md
│   └── usage.md
├── examples/
│   └── basic_workflow.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Getting Help

- **[Installation](./installation.md)** — System setup, dependencies, llama-server
- **[Usage](./usage.md)** — Commands, configuration, troubleshooting
- **[Examples](../examples/basic_workflow.md)** — Real-world patterns

## Platform Support

| OS | Status | Notes |
|---|---|---|
| Windows | ✅ In dev, auto-config to `%APPDATA%\sequence-llm\config.yaml` |
| macOS | ✅ Auto-config to `~/Library/Application Support/sequence-llm/config.yaml` |
| Linux | ✅ Auto-config to `~/.config/sequence-llm/config.yaml` |

## License

MIT — See [LICENSE](../LICENSE)

