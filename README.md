# Sequence-LLM

Sequence-LLM is a terminal-first CLI for running local LLMs through `llama-server` (llama.cpp) with profile-based model switching and automatic server lifecycle management.

It is designed for developers who run multiple local models and want a simple, reproducible workflow without writing shell scripts.

Cross-platform: Windows, Linux, macOS.

## Why Sequence-LLM

Running local models often involves:

- Manually starting and stopping servers
- Remembering model paths and ports
- Managing multiple configurations
- Writing ad-hoc scripts to switch models

Sequence-LLM solves this by providing:

- Named model profiles
- Automatic start and shutdown of servers
- Interactive chat interface
- Consistent configuration across machines

## Features

- Interactive CLI built with Typer and Rich
- Profile-based model switching (`/brain`, `/coder`, etc.)
- Automatic shutdown of previous server before starting a new one
- Health checking with readiness polling
- Cross-platform process management using subprocess and psutil
- OS-aware configuration directory creation
- Conversation history management
- Status panel showing active model and server info

## Installation

### Requirements

- Python 3.9+
- `llama-server` binary from llama.cpp

Install from PyPI:

```bash
pip install sequence-llm
```

## Quick Start

Run the CLI:

```bash
seq-llm
```

On first launch, a configuration file is created automatically.

Config locations:

- Windows: `%APPDATA%\sequence-llm\config.yaml`
- Linux: `~/.config/sequence-llm/config.yaml`
- macOS: `~/Library/Application Support/sequence-llm/config.yaml`

## Configuration Example

```yaml
llama_server: "/path/to/llama-server"

defaults:
  threads: 6
  threads_batch: 8
  batch_size: 512

profiles:
  brain:
    name: "Brain Model"
    model_path: "/path/to/model.gguf"
    system_prompt: "/path/to/system.txt"
    port: 8081
    ctx_size: 16384
    temperature: 0.7

  coder:
    name: "Coder Model"
    model_path: "/path/to/coder.gguf"
    system_prompt: "/path/to/coder.txt"
    port: 8082
    ctx_size: 32768
    temperature: 0.3
```

## CLI Usage

```
/status   → show active model and server status
/brain    → switch to brain profile
/coder    → switch to coder profile
/clear    → clear conversation history
/quit     → stop server and exit
```

Typing any text sends a message to the active model.

## Example Workflow

1. Start CLI
2. Automatically load default model
3. Switch between models using commands
4. Chat interactively without restarting processes manually

## Architecture

Core components:

- CLI: interactive interface and command routing
- Server Manager: lifecycle control of llama-server
- API Client: communication with local inference server
- Config System: YAML-based profiles and defaults

## Development

Clone repository:

```bash
git clone https://github.com/Ananay28425/Sequence-LLM.git
cd Sequence-LLM
pip install -e .
```

Run tests:

```bash
pytest -v
```

## License

MIT License. See LICENSE file for details.

## Contributing

Pull requests and issues are welcome.

GitHub: https://github.com/Ananay28425/Sequence-LLM

## Support

Report bugs or request features:
https://github.com/Ananay28425/Sequence-LLM/issues

---

Sequence-LLM provides a lightweight and predictable way to manage local LLM workflows from the terminal.

---

**Sequence-LLM** - Orchestrate LLM sequences with ease.