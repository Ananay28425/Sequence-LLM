#!/usr/bin/env python3
"""Quick test of config loading and command builder."""

from seq_llm.config import Config, ensure_default_config
from seq_llm.core.command_builder import build_llama_server_command

# Load config
config_path = ensure_default_config()
print(f"Config path: {config_path}")
config = Config.from_yaml(config_path)

print(f"llama_server: {config.llama_server}")
print(f"profiles: {list(config.models.keys())}")

# Test command building for brain profile
brain = config.get_model("brain")
if brain:
    print(f"\nBrain profile:")
    print(f"  name: {brain.name}")
    print(f"  endpoint: {brain.endpoint}")
    print(f"  port: {brain.port}")
    print(f"  ctx_size: {brain.ctx_size}")
    print(f"  threads: {brain.threads}")
    
    try:
        cmd = build_llama_server_command(config.llama_server, brain, config.defaults)
        print(f"\nBuilt command:")
        print(" ".join(cmd))
    except Exception as e:
        print(f"Error building command: {e}")

# Test coder profile
coder = config.get_model("coder")
if coder:
    print(f"\n\nCoder profile:")
    print(f"  name: {coder.name}")
    print(f"  port: {coder.port}")
    print(f"  ctx_size: {coder.ctx_size}")
    
    try:
        cmd = build_llama_server_command(config.llama_server, coder, config.defaults)
        print(f"\nBuilt command:")
        print(" ".join(cmd))
    except Exception as e:
        print(f"Error building command: {e}")
