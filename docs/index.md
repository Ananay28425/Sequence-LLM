# Sequence-LLM Documentation

Welcome to the Sequence-LLM documentation. This project provides a command-line tool for managing and interacting with local language models through an OpenAI-compatible API.

## Table of Contents

- [Installation](./installation.md) - Get started with Sequence-LLM
- [Usage](./usage.md) - Learn how to use the CLI and API client
- [Examples](../examples/basic_workflow.md) - Practical examples and workflows

## Quick Start

```bash
# Install the package
pip install -e .

# Start the server
seq-llm start

# In another terminal, use the client
seq-llm chat --model llama2 "What is machine learning?"
```

## Features

- **Process Management**: Automatically manage language model server processes
- **Port Management**: Intelligent port allocation and management
- **OpenAI-Compatible API**: Use any OpenAI-compatible client library
- **Configuration Management**: Simple YAML-based configuration
- **CLI Interface**: User-friendly command-line interface

## Architecture

Sequence-LLM consists of three main components:

1. **Server Manager** (`core/server_manager.py`) - Handles process lifecycle and port management
2. **API Client** (`core/api_client.py`) - Provides OpenAI-compatible client
3. **Configuration** (`config.py`) - Manages all configuration and models
4. **CLI** (`cli.py`) - Single entry point for all commands

## Configuration

Sequence-LLM uses YAML configuration files to define models and settings. See [Usage](./usage.md) for details on configuration format.

## Support

For issues, questions, or contributions, please visit the project repository.
