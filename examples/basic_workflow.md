# Basic Workflow Example

This example demonstrates a simple workflow using Sequence-LLM to manage and interact with local LLM servers.

## Overview

Sequence-LLM allows you to:
1. Configure and manage local LLM servers
2. Start/stop servers on demand
3. Query multiple models through a unified API
4. Chain operations together in sequences

## Setup

First, install Sequence-LLM:

```bash
pip install sequence-llm
```

## Configuration

Create a `config.yaml` file with your model configurations:

```yaml
models:
  - name: "mistral"
    server_url: "http://localhost:8000"
    port: 8000
    cmd: "ollama serve mistral"
    
  - name: "llama2"
    server_url: "http://localhost:8001"
    port: 8001
    cmd: "ollama serve llama2"
```

## Basic Usage

### Starting a Server

```python
from seq_llm import SequenceLLM

llm = SequenceLLM(config_path="config.yaml")

# Start a specific model server
llm.start_server("mistral")

# Query the model
response = llm.query("mistral", "What is machine learning?")
print(response)

# Stop the server
llm.stop_server("mistral")
```

### Chaining Operations

```python
from seq_llm import SequenceLLM

llm = SequenceLLM(config_path="config.yaml")

# Start multiple servers
llm.start_server("mistral")
llm.start_server("llama2")

# Chain queries together
prompt1 = "Explain quantum computing"
result1 = llm.query("mistral", prompt1)

# Use first result as input for second
prompt2 = f"Summarize this in one sentence: {result1}"
result2 = llm.query("llama2", prompt2)

print("Mistral Response:", result1)
print("Llama2 Summary:", result2)

# Cleanup
llm.stop_all_servers()
```

## Advanced Features

### Server Health Checks

```python
if llm.is_server_running("mistral"):
    response = llm.query("mistral", "Hello!")
else:
    print("Server is not running")
```

### Custom Parameters

```python
response = llm.query(
    "mistral",
    "Generate creative content",
    temperature=0.8,
    max_tokens=200
)
```

## Troubleshooting

### Server Won't Start

- Ensure the model is installed (e.g., `ollama pull mistral`)
- Check that the specified port is not already in use
- Review server logs for error messages

### Connection Errors

- Verify `server_url` matches the running server
- Check firewall settings
- Ensure the server is fully started before querying

## Next Steps

- See [Usage Guide](../docs/usage.md) for detailed API documentation
- Check [Installation Guide](../docs/installation.md) for platform-specific setup
- Review [Configuration](../docs/index.md) for advanced options
