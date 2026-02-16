#!/usr/bin/env python3
"""Test CLI startup without the interactive loop."""

import sys
from pathlib import Path

# Test imports
try:
    from seq_llm.config import Config, ensure_default_config
    from seq_llm.core.command_builder import build_llama_server_command
    from seq_llm.cli import CLIState
    print("[✓] All imports successful")
except Exception as e:
    print(f"[✗] Import error: {e}")
    sys.exit(1)

# Test config loading
try:
    config_path = ensure_default_config()
    config = Config.from_yaml(config_path)
    print(f"[✓] Config loaded from {config_path}")
    print(f"    llama_server: {config.llama_server}")
    print(f"    profiles: {list(config.models.keys())}")
except Exception as e:
    print(f"[✗] Config error: {e}")
    sys.exit(1)

# Test CLIState initialization
try:
    state = CLIState()
    state.load_config()
    print(f"[✓] CLIState initialized and config loaded")
    print(f"    Profiles available: {list(state.config.models.keys())}")
except Exception as e:
    print(f"[✗] CLIState error: {e}")
    sys.exit(1)

# Test command building (without actually starting server)
try:
    brain = state.config.get_model("brain")
    if brain:
        cmd = build_llama_server_command(state.config.llama_server, brain, state.config.defaults)
        print(f"[✓] Command builder works:")
        print(f"    {' '.join(cmd[:3])}...")
except Exception as e:
    print(f"[✗] Command builder error: {e}")
    sys.exit(1)

print("\n[✓✓✓] All checks passed! CLI is ready to use.")
