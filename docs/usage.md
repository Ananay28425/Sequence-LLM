# Usage Guide

## Getting Started

After installing `seq-llm`, launch the interactive CLI:

```bash
seq-llm
```

On first run, a default config is created at:
- **Windows**: `%APPDATA%\sequence-llm\config.yaml`
- **Linux**: `~/.config/sequence-llm/config.yaml`
- **macOS**: `~/Library/Application Support/sequence-llm/config.yaml`

The CLI attempts to auto-start the `brain` profile.

## Configuration

### Default Config Location

Edit the auto-created config at your OS-specific path (see above). A fresh config looks like:

```yaml
llama_server: "<path to llama-server>"

defaults:
  threads: 6
  threads_batch: 8
  batch_size: 512

profiles:
  brain:
    name: "Brain (GLM-4.7-Flash)"
    model_path: "<path>"
    system_prompt: "<path>"
    port: 8081
    ctx_size: 16384
    temperature: 0.7

  coder:
    name: "Coder (Qwen2.5-Coder-7B)"
    model_path: "<path>"
    system_prompt: "<path>"
    port: 8082
    ctx_size: 32768
    temperature: 0.3
```

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `llama_server` | string | Path to the `llama-server` binary |
| `defaults` | object | Default CLI args (threads, batch_size, etc.) |
| `profiles` | object | Named model profiles |
| `profiles.[name].name` | string | Human-readable profile name |
| `profiles.[name].model_path` | string | Path to .gguf or model file |
| `profiles.[name].system_prompt` | string | Path to system prompt file (plaintext) |
| `profiles.[name].port` | int | Port for this profile's server |
| `profiles.[name].ctx_size` | int | Context window size (tokens) |
| `profiles.[name].temperature` | float | Sampling temperature (0.0–2.0) |

## Interactive Commands

Once the CLI is running, use these commands:

| Command | Behavior |
|---------|----------|
| `/brain` | Switch to brain profile (stops current server, starts brain) |
| `/coder` | Switch to coder profile |
| `/status` | Display active model, port, PID, uptime (Rich Panel) |
| `/clear` | Clear conversation history (does NOT stop server) |
| `/quit`, `/exit` | Stop server and exit CLI |
| `(any text)` | Send chat message to active model (prefixed: "Brain> ...") |

### Example Session

```
Sequence-LLM v0.1
Attempting to start 'brain' profile...
✓ Brain (GLM-4.7-Flash) started on port 8081
Ready for input. Commands: /brain, /coder, /status, /clear, /quit, /exit

You> /status
╭─ Server Status ─╮
│ Active: Brain (GLM-4.7-Flash)     
│ Port: 8081     
│ Health: ✓ Ready │
╰──────────────────╯

You> Hello, what is 2+2?
Brain> 2 + 2 = 4

You> /coder
Stopping server...
Starting Coder (Qwen2.5-Coder-7B)...
✓ Coder (Qwen2.5-Coder-7B) started on port 8082

You> Write me a Python function to add two numbers
Coder> def add(a, b):
    return a + b

You> /quit
Goodbye!
```

## Using Multiple Profiles

Create as many profiles as you need in `config.yaml`:

```yaml
profiles:
  brain:
    name: "Brain"
    model_path: "/models/brain.gguf"
    port: 8081
    # ...
  
  coder:
    name: "Coder"
    model_path: "/models/coder.gguf"
    port: 8082
    # ...
  
  analyst:
    name: "Data Analyst"
    model_path: "/models/analyst.gguf"
    port: 8083
    # ...
```

Switch between them at runtime:

```
You> /analyst
Stopping server...
Starting Data Analyst...
✓ Data Analyst started on port 8083
```

## Python API (Advanced)

Use the library programmatically:

```python
from seq_llm.config import Config
from seq_llm.core.server_manager import ServerManager
from seq_llm.core.api_client import APIClient
from pathlib import Path

# Load config
config = Config.from_yaml(Path.home() / ".config/sequence-llm/config.yaml")

# Get a profile
profile = config.get_model("brain")

# Start server
manager = ServerManager(
    server_command=["llama-server", "-m", profile.endpoint],
    port=profile.model_type,  # Adjust as needed
    timeout=30
)
manager.start()
manager.wait_for_ready()

# Send chat via API
client = APIClient(base_url=manager.get_base_url())
for chunk in client.stream_chat(
    messages=[{"role": "user", "content": "Hello!"}],
    model="local"
):
    print(chunk, end="", flush=True)

# Cleanup
manager.stop()
client.close()
```

## Troubleshooting

### Issue: "No model running. Use /brain or /coder first."

**Cause**: Typed a chat message before starting a profile.

**Solution**: Run `/brain` or `/coder` first.

### Issue: Health check timeout on profile startup

**Cause**: 
- `llama-server` path is incorrect or binary not found
- Model path does not exist
- Port is already in use (conflict with another process)

**Solution**:
1. Verify `llama_server` path in config: `ls /path/to/llama-server`
2. Verify model path: `ls /path/to/model.gguf`
3. Check port availability: `lsof -i :8081` (macOS/Linux) or `netstat -ano | findstr :8081` (Windows)
4. Try starting `llama-server` manually to see detailed error logs

### Issue: "Profile 'X' not found"

**Cause**: Profile name not in `config.yaml` under `profiles`.

**Solution**: Add the profile or use an existing one (`/brain` or `/coder`).

### Issue: Slow model startup

The health check polls `/health` every 1 second for up to 30 seconds. Large models may take longer.

**Solution**: Increase `timeout` in `ServerManager` instantiation (Python API) or wait longer (CLI will eventually show failure).

## Performance Tips

1. **Pre-load common profiles**: Start with the profile you use most often to avoid cold-start wait times
2. **Tune context size**: Smaller `ctx_size` = faster inference
3. **Use moderate temperature**: 0.0 = deterministic, 0.7 = balanced, 1.0+ = more creative
4. **Monitor resources**: Use system monitor or `psutil` to watch CPU/memory during inference

