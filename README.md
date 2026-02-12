# Sequence-LLM

A lightweight Python framework for orchestrating sequences of LLM API calls with local server management and configuration-driven workflows.

## Overview

Sequence-LLM simplifies working with Large Language Models by providing:

- **Configuration-driven workflows**: Define LLM sequences in YAML
- **Local server management**: Automatic startup/shutdown of compatible LLM servers
- **OpenAI-compatible API**: Works with any OpenAI-compatible LLM endpoint
- **Simple CLI**: Easy command-line interface for running workflows
- **Process lifecycle management**: Handles server processes cleanly

## Features

- 🔧 **Zero-configuration setup** - sensible defaults for quick start
- 🚀 **Automatic server management** - spawn and manage LLM servers
- 📝 **YAML-based configuration** - define workflows declaratively
- 🔌 **OpenAI-compatible** - works with Ollama, LM Studio, vLLM, and more
- ✅ **Clean process handling** - proper lifecycle and resource cleanup
- 🧪 **Well-tested** - comprehensive unit tests included

## Installation

### Requirements

- Python 3.8 or higher
- pip or pip3

### From source

```bash
git clone https://github.com/yourusername/Sequence-LLM.git
cd Sequence-LLM
pip install -e .
```

## Quick Start

### 1. Create a configuration file (`config.yaml`)

```yaml
server:
  host: localhost
  port: 11434
  type: ollama
  
models:
  - name: llama2
    prompt: "Explain quantum computing"
  - name: mistral
    prompt: "What are the implications?"
```

### 2. Run a workflow

```bash
seq-llm run config.yaml
```

## Configuration

See [Configuration Documentation](docs/index.md) for detailed options.

### Basic Structure

```yaml
server:
  host: localhost
  port: 11434
  type: ollama  # or custom

models:
  - name: model-name
    prompt: "Your prompt here"
    temperature: 0.7
    max_tokens: 512
```

## Usage Examples

### Python API

```python
from seq_llm.core.api_client import OpenAIClient
from seq_llm.config import load_config

config = load_config('config.yaml')
client = OpenAIClient(config.server)

response = client.chat_completion(
    model='llama2',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response)
```

### Command Line

```bash
# Run a workflow
seq-llm run config.yaml

# Show configuration
seq-llm config config.yaml

# Start/stop server manually
seq-llm server start --host localhost --port 11434
seq-llm server stop
```

## Project Structure

```
Sequence-LLM/
├── src/seq_llm/          # Main package
│   ├── cli.py            # CLI entry point
│   ├── config.py         # Configuration management
│   └── core/
│       ├── server_manager.py   # Process lifecycle
│       └── api_client.py       # API client
├── tests/                # Test suite
├── docs/                 # Documentation
├── examples/             # Example workflows
└── README.md            # This file
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [API Documentation](docs/index.md)
- [Examples](examples/)

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

### Building Documentation

```bash
cd docs
# Documentation uses Markdown
```

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

## Roadmap

- [ ] Support for model chaining and complex workflows
- [ ] Web UI for workflow visualization
- [ ] Integration with more LLM providers
- [ ] Performance optimization and caching
- [ ] Advanced error handling and retries

---

**Sequence-LLM** - Orchestrate LLM sequences with ease.
