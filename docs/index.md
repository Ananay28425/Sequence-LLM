# Sequence-LLM Documentation

A terminal-first CLI for managing local LLMs via `llama-server`. Ensures only one model runs at a time with seamless profile switching.

## Table of Contents

- [Installation](./installation.md) - Setup and dependencies
- [Usage](./usage.md) - Interactive CLI, configuration, and commands
- [Examples](../examples/basic_workflow.md) - Sample workflows and patterns

## Quick Start

```bash
# 1. Install
pip install sequence-llm

# 2. Launch interactive CLI
seq-llm

# 3. On first run, a config is created at:
#    - Windows: %APPDATA%\sequence-llm\config.yaml
#    - Linux:   ~/.config/sequence-llm/config.yaml
#    - macOS:   ~/Library/Application Support/sequence-llm/config.yaml

# 4. Edit the config to point to your llama-server and models

# 5. Use commands:
#    /brain    - switch to brain profile
#    /coder    - switch to coder profile
#    /status   - show active model status
#    /clear    - clear conversation history
#    /quit     - stop server and exit
#    (text)    - send chat message to active model
```

## Key Features

- Profile-based profiles: Define named profiles (brain, coder, etc.) in YAML
- Interactive CLI: Typer + Rich for a modern terminal UI
- Sequential loading: Only one `llama-server` at a time; switching stops the old server
- Auto-config: Creates sensible defaults on first run
- Status panel: Rich-formatted output showing active model, port, health
- Safe shutdown: Graceful SIGTERM then SIGKILL on profile switch or exit
- Log capture: Server stdout and stderr are written to user logs for diagnostics
- Context safety guard: Prevents conversation overflow of model context window
- Cross-platform: Windows, Linux, macOS

## Architecture

Three core modules:

1. Config (`config.py`) - Load and validate YAML profiles, OS-aware config paths
2. ServerManager (`core/server_manager.py`) - Start and stop `llama-server`, health polling, log capture
3. APIClient (`core/api_client.py`) - Stream chat completions via `httpx`
4. CLI (`cli.py`) - Typer and Rich interactive loop

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

- CLI: Typer + Rich
- Config: dataclasses + pyyaml
- Process: subprocess + psutil
- HTTP: httpx (sync streaming)
- Tests: pytest

## File Structure

```
sequence-llm/
├── src/seq_llm/
│   ├── cli.py
│   ├── config.py
│   └── core/
│       ├── server_manager.py
│       └── api_client.py
├── tests/
├── docs/
│   ├── index.md
│   ├── installation.md
│   └── usage.md
├── examples/
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

- See [Installation](./installation.md)
- See [Usage](./usage.md)
- See [Examples](../examples/basic_workflow.md)

## Platform Support

| OS      | Status    | Notes                                                                 |
| ------- | --------- | --------------------------------------------------------------------- |
| Windows | Supported | Config path: `%APPDATA%\sequence-llm\config.yaml`                     |
| macOS   | Supported | Config path: `~/Library/Application Support/sequence-llm/config.yaml` |
| Linux   | Supported | Config path: `~/.config/sequence-llm/config.yaml`                     |

## License

AGPL 3.0 - See LICENSE
