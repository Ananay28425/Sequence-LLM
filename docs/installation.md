# Installation

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## From Source

Clone the repository:

```bash
git clone https://github.com/yourusername/Sequence-LLM.git
cd Sequence-LLM
```

Install in development mode:

```bash
pip install -e .
```

Or install with all development dependencies:

```bash
pip install -e ".[dev]"
```

## From PyPI

Once published, you can install directly:

```bash
pip install sequence-llm
```

## Verify Installation

Check that the CLI is available:

```bash
seq-llm --version
seq-llm --help
```

## Dependencies

The package requires:
- `openai>=0.27.0` - OpenAI API client
- `pyyaml>=6.0` - YAML configuration parsing
- `click>=8.0` - CLI framework
- `requests>=2.28.0` - HTTP library

## Troubleshooting

### Command not found: seq-llm

If the CLI command is not found after installation, try:

1. Ensure the Python Scripts directory is in your PATH
2. Reinstall the package: `pip install --force-reinstall -e .`
3. Check your Python environment: `which python` (or `where python` on Windows)

### Import errors

If you encounter import errors, verify your installation:

```bash
python -c "import seq_llm; print(seq_llm.__version__)"
```

### Virtual Environment (Recommended)

It's recommended to use a virtual environment:

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

pip install -e .
```
