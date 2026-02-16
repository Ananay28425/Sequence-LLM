# Basic Workflow Example

Learn how to use the Sequence-LLM interactive CLI and Python API for managing local LLM models.

## Scenario: Research Assistant with Multiple Profiles

We have two profiles:
- **brain**: Fast, conversational GLM-4.7-Flash (~7B)
- **coder**: Specialized Qwen2.5-Coder-7B for code generation

We want to ask the "brain" for context, then the "coder" to generate code, then back to "brain" to discuss it.

## Step 1: Install and Configure

```bash
pip install -e .
seq-llm
```

On first launch, a config is created. Edit it with your paths:

```yaml
llama_server: "/opt/llama-server/llama-server"

defaults:
  threads: 6
  threads_batch: 8
  batch_size: 512

profiles:
  brain:
    name: "Brain (GLM-4.7-Flash)"
    model_path: "/models/glm-4.7-flash.gguf"
    system_prompt: "/prompts/brain_system.txt"
    port: 8081
    ctx_size: 16384
    temperature: 0.7

  coder:
    name: "Coder (Qwen2.5-Coder)"
    model_path: "/models/qwen-coder-7b.gguf"
    system_prompt: "/prompts/coder_system.txt"
    port: 8082
    ctx_size: 32768
    temperature: 0.3
```

## Step 2: Interactive Workflow

```
$ seq-llm

Sequence-LLM v0.1
Attempting to start 'brain' profile...
✓ Brain (GLM-4.7-Flash) started on port 8081
Ready for input. Commands: /brain, /coder, /status, /clear, /quit, /exit

You> /status
╭─ Server Status ──╮
│ Active: Brain (GLM-4.7-Flash)
│ Port: 8081
│ Health: ✓ Ready
╰──────────────────╯

You> What are the best practices for REST API design?
Brain> REST API best practices include:
  1. Use standard HTTP methods (GET, POST, PUT, DELETE)
  2. Structure URLs as resources (e.g., /api/users/{id})
  3. Use appropriate status codes (200, 404, 500, etc.)
  4. Implement pagination for large datasets
  5. Add API versioning (e.g., /api/v1/)
  6. Use content negotiation (Accept: application/json)
  [...]

You> /coder
Stopping server...
Starting Coder (Qwen2.5-Coder)...
✓ Coder (Qwen2.5-Coder) started on port 8082

You> Write a Python Flask REST API following those principles
Coder> from flask import Flask, jsonify, request
app = Flask(__name__)

# Mock database
users = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
]

@app.route('/api/v1/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page
    end = start + per_page
    return jsonify({
        "data": users[start:end],
        "page": page,
        "total": len(users)
    }), 200

@app.route('/api/v1/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name required"}), 400
    user = {"id": len(users) + 1, "name": data['name']}
    users.append(user)
    return jsonify(user), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)

You> /brain
Stopping server...
Starting Brain (GLM-4.7-Flash)...
✓ Brain (GLM-4.7-Flash) started on port 8081

You> What are the security considerations for this API?
Brain> Important security considerations for the Flask REST API:
  1. **Input Validation**: The create_user endpoint should validate/sanitize data
  2. **Authentication**: Add JWT or OAuth2 for secure endpoints
  3. **Rate Limiting**: Prevent abuse with rate limiting middleware
  4. **HTTPS**: Always use HTTPS in production
  5. **CORS**: Configure Cross-Origin Resource Sharing carefully
  6. **Error Handling**: Don't leak sensitive info in error messages
  [...]

You> /quit
Goodbye!
```

## Step 3: Python API (Programmatic)

For automation or integration:

```python
from seq_llm.config import Config
from seq_llm.core.server_manager import ServerManager
from seq_llm.core.api_client import APIClient
from pathlib import Path

# Load config
config_path = Path.home() / ".config/sequence-llm/config.yaml"
config = Config.from_yaml(config_path)

# Function to chat with a profile
def chat_with_profile(profile_name: str, user_message: str):
    profile = config.get_model(profile_name)
    if not profile:
        print(f"Profile {profile_name} not found")
        return None
    
    # Start server for this profile
    manager = ServerManager(
        server_command=["llama-server", "-m", profile.endpoint],
        port=8000,  # In real use, read from profile config
        timeout=30
    )
    manager.start()
    
    if not manager.wait_for_ready(timeout=30):
        print(f"Failed to start {profile_name}")
        return None
    
    # Stream chat
    client = APIClient(base_url=manager.get_base_url())
    full_response = ""
    
    print(f"{profile.name}> ", end="", flush=True)
    for chunk in client.stream_chat(
        messages=[{"role": "user", "content": user_message}],
        model="local"
    ):
        print(chunk, end="", flush=True)
        full_response += chunk
    print()
    
    # Cleanup
    manager.stop()
    client.close()
    
    return full_response

# Run the workflow
print("=== Asking Brain ===")
brain_response = chat_with_profile("brain", "What is machine learning?")

print("\n=== Asking Coder ===")
coder_response = chat_with_profile(
    "coder",
    f"Implement a machine learning classifier based on: {brain_response[:200]}"
)

print("\n=== Summary from Brain ===")
summary = chat_with_profile(
    "brain",
    f"Briefly summarize this implementation: {coder_response[:200]}"
)
```

## Key Takeaways

1. **CLI for interactive use**: Type messages naturally, switch profiles with `/coder`, `/brain`
2. **Python API for automation**: Programmatically manage servers and stream responses
3. **Sequential loading**: Only one server at a time — switching is automatic
4. **Health checks**: Built-in polling ensures model is ready before use
5. **Config-driven**: All profiles in YAML, auto-creates default config on first run

## Tips

- **Large models**: Increase `timeout` if startup takes >30s
- **Debug output**: Run `llama-server` manually first to test command syntax
- **Multiple profiles**: Add as many profiles as you need in `config.yaml`
- **Conversation history**: Use `/clear` to wipe chat history without stopping the server
- **Port conflicts**: Edit profile ports in config if they're already in use

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
