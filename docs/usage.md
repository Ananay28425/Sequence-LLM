# Usage Guide

## Installation

First, install the package:

```bash
pip install -e .
```

## Basic Usage

### Command Line Interface

Sequence-LLM provides a single entry point through the CLI:

```bash
seq-llm [command] [options]
```

### Starting a Server

To start an LLM server:

```bash
seq-llm start --model gpt-4 --port 8000
```

Available options:
- `--model`: The model to use (required)
- `--port`: Port to run the server on (default: 8000)
- `--config`: Path to configuration file (optional)

### Making Requests

Once the server is running, you can make requests using the OpenAI-compatible API:

```python
from openai import OpenAI

client = OpenAI(api_key="sk-test", base_url="http://localhost:8000/v1")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Configuration Files

Create a `config.yaml` file to define your LLM models:

```yaml
models:
  - name: gpt-4
    type: openai
    api_key: ${OPENAI_API_KEY}
  - name: local-model
    type: local
    path: /path/to/model

server:
  default_port: 8000
  host: 0.0.0.0
```

Then use it:

```bash
seq-llm start --config config.yaml --model gpt-4
```

## Advanced Examples

### Batch Processing

Process multiple requests in sequence:

```python
from seq_llm import Sequence

seq = Sequence(model="gpt-4")

results = []
for prompt in prompts:
    response = seq.chat(messages=[{"role": "user", "content": prompt}])
    results.append(response)
```

### Environment Variables

Use environment variables for sensitive configuration:

```bash
export OPENAI_API_KEY=sk-xxxxx
seq-llm start --model gpt-4
```

## Troubleshooting

### Port Already in Use

If the port is already in use, specify a different one:

```bash
seq-llm start --model gpt-4 --port 8001
```

### Connection Issues

Verify the server is running:

```bash
curl http://localhost:8000/health
```

### API Key Issues

Ensure your API keys are properly set in the configuration or environment variables.
