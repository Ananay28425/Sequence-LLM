# test_cli_manual.py
from seq_llm.config import Config, ensure_default_config
from pathlib import Path

# Test config loading
config_path = ensure_default_config()
print(f"Config created at: {config_path}")

config = Config.from_yaml(config_path)
print(f"Profiles found: {[m.name for m in config.models.values()]}")

# Test profile access
brain = config.get_model("brain")
if brain:
    print(f"Brain profile: {brain.name}, endpoint: {brain.endpoint}")
else:
    print("Brain profile not found (expected if config defaults are used)")