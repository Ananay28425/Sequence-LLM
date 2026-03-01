# Sequence-LLM

Sequence-LLM is a **terminal-first orchestration tool** for running local large language models through `llama.cpp` (`llama-server`) with automatic server lifecycle management, profile-based switching, and reproducible workflows.

It removes the need to manually start servers, remember commands, or write shell scripts when working with multiple models.

Sequence-LLM works with **any hardware supported by llama.cpp** — CPU, CUDA GPUs, ROCm, Metal, and more.

Cross-platform: Windows, Linux, macOS.

---

## Why Sequence-LLM

Running local models often involves:

- Manually starting and stopping servers
- Remembering model paths and ports
- Managing multiple configurations
- Writing ad-hoc scripts to switch models
- Repeating setup across machines

Sequence-LLM solves this by providing:

- Named model profiles
- Automatic start and shutdown of servers
- Interactive chat interface
- Consistent configuration across machines
- Deterministic, script-free workflows

---

## Who Is This For

- Developers running multiple local models
- AI engineers building local pipelines
- Researchers comparing architectures
- Self-hosting enthusiasts
- GPU workstation users
- CLI-first workflows

If you use tools like `llama.cpp`, with upcoming support for Ollama, LM Studio, or custom scripts - Sequence-LLM simplifies the workflow.

---

## Features

- Interactive CLI built with Typer and Rich
- Profile-based model switching (`/brain`, `/coder`, etc.)
- Automatic shutdown of previous server before starting a new one
- Health checking with readiness polling
- Context-window safety guard (prevents overflow / crashes)
- Cross-platform process management using subprocess and psutil
- OS-aware configuration directory creation
- Conversation history management
- Status panel showing active model and server info
- First-run configuration wizard

---

## Hardware Support

Sequence-LLM does **not** perform inference itself.

It orchestrates `llama-server`, meaning it works with:

- CPU inference
- NVIDIA CUDA GPUs
- AMD ROCm GPUs
- Apple Metal
- Any backend supported by llama.cpp

---

## Comparison with Other Tools

| Tool          | Primary Focus | Sequence-LLM Advantage             |
| ------------- | ------------- | ---------------------------------- |
| Ollama        | Easy installs | Multi-model orchestration workflow |
| LM Studio     | GUI           | Lightweight CLI automation         |
| Raw llama.cpp | Flexible      | No manual scripts needed           |
| Open-WebUI    | Web UI        | Minimal overhead terminal workflow |

Sequence-LLM sits between simplicity and flexibility.

---

## Installation

### Requirements

- Python 3.9+
- `llama-server` binary from llama.cpp

Install from PyPI:

```bash
pip install sequence-llm
```

---

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

---

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

---

## CLI Usage

```
/status   → show active model and server status
/brain    → switch to brain profile
/coder    → switch to coder profile
/clear    → clear conversation history
/quit     → stop server and exit
```

Typing any text sends a message to the active model.

---

## Example Workflow

1. Start CLI
2. Automatically load default model
3. Switch between models using commands
4. Chat interactively without restarting processes manually

---

## Architecture

```
User → CLI → ServerManager → llama-server → Model
           ↑
        Config + Profiles
```

Core components:

- CLI - interactive interface and command routing
- Server Manager - lifecycle control of llama-server
- API Client - communication with local inference server
- Config System - YAML-based profiles and defaults

---

## Roadmap

Planned evolution:

- v0.3 — Multi-model named workflows
- v0.4 — TUI interface
- v0.5 — Hardware auto-optimization
- v1.0 — Production stability

---

## For Development and Contributors

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

---

## License

AGPL-3.0 License. See LICENSE file for details.

---

## Contributing

Pull requests and issues are welcome.

GitHub: https://github.com/Ananay28425/Sequence-LLM

---

Sequence-LLM provides a lightweight and predictable way to manage local LLM workflows from the terminal.

Sequence-LLM - Orchestrate LLM workflows with ease.
