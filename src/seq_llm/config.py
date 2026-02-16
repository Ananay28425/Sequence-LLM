"""Configuration management for Sequence-LLM.

Implements dataclasses and loader utilities used by unit tests and the CLI.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# --- dataclasses -----------------------------------------------------------
@dataclass
class ModelConfig:
    name: str
    model_type: str
    endpoint: str
    api_key: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    port: int = 8000
    ctx_size: int = 2048
    threads: int = 6
    ngl: int = 0
    top_p: float = 0.95

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Model name must not be empty")
        if not self.model_type:
            raise ValueError("Model type must not be empty")
        if not self.endpoint:
            raise ValueError("Model endpoint must not be empty")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1

    def __post_init__(self) -> None:
        if not (1 <= int(self.port) <= 65535):
            raise ValueError("port must be in range 1..65535")
        if int(self.workers) <= 0:
            raise ValueError("workers must be > 0")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Config:
    server: ServerConfig
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    default_model: Optional[str] = None
    llama_server: str = ""
    defaults: Dict[str, Any] = field(default_factory=dict)

    # --- construction / serialization -------------------------------------
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        server_data = data.get("server", {})
        server = ServerConfig(
            host=server_data.get("host", "127.0.0.1"),
            port=server_data.get("port", 8000),
            workers=server_data.get("workers", 1),
        )

        # Support both legacy `models` (list) and the preferred `profiles` mapping
        models_raw = data.get("models") if data.get("models") is not None else data.get("profiles", [])
        models: Dict[str, ModelConfig] = {}
        defaults = data.get("defaults", {})

        # If profiles is a mapping (dict), keys are profile names
        if isinstance(models_raw, dict):
            for name, m in models_raw.items():
                # derive endpoint: prefer explicit endpoint/base_url/model_path, else use localhost:port
                endpoint = (
                    m.get("endpoint")
                    or m.get("base_url")
                    or m.get("model_path")
                    or (f"http://localhost:{m.get('port')}" if m.get("port") else None)
                )
                models[name] = ModelConfig(
                    name=name,
                    model_type=(m.get("model_type") or m.get("provider") or m.get("type") or "local"),
                    endpoint=endpoint or "",
                    api_key=m.get("api_key"),
                    temperature=m.get("temperature", 0.7),
                    max_tokens=m.get("max_tokens", 2048),
                    port=m.get("port", defaults.get("port", 8000)),
                    ctx_size=m.get("ctx_size", defaults.get("ctx_size", 2048)),
                    threads=m.get("threads", defaults.get("threads", 6)),
                    ngl=m.get("ngl", defaults.get("ngl", 0)),
                    top_p=m.get("top_p", defaults.get("top_p", 0.95)),
                )
        else:
            # assume a list of model entries
            for m in models_raw:
                name = m.get("name")
                # derive endpoint: prefer explicit endpoint/base_url/model_path, else use localhost:port
                endpoint = (
                    m.get("endpoint") 
                    or m.get("base_url") 
                    or m.get("model_path")
                    or (f"http://localhost:{m.get('port')}" if m.get("port") else None)
                )
                models[name] = ModelConfig(
                    name=name,
                    model_type=(m.get("model_type") or m.get("provider") or m.get("type") or "local"),
                    endpoint=endpoint or "",
                    api_key=m.get("api_key"),
                    temperature=m.get("temperature", 0.7),
                    max_tokens=m.get("max_tokens", 2048),
                    port=m.get("port", defaults.get("port", 8000)),
                    ctx_size=m.get("ctx_size", defaults.get("ctx_size", 2048)),
                    threads=m.get("threads", defaults.get("threads", 6)),
                    ngl=m.get("ngl", defaults.get("ngl", 0)),
                    top_p=m.get("top_p", defaults.get("top_p", 0.95)),
                )

        cfg = cls(
            server=server,
            models=models,
            default_model=data.get("default_model"),
            llama_server=data.get("llama_server", ""),
            defaults=defaults,
        )
        return cfg

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        p = Path(path)
        with p.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return cls.from_dict(raw)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server": self.server.to_dict(),
            # keep external representation as a list for compatibility
            "models": [m.to_dict() for m in self.models.values()],
            "default_model": self.default_model,
        }

    # --- helpers ---------------------------------------------------------
    def get_model(self, name: str) -> Optional[ModelConfig]:
        return self.models.get(name)


# --- OS-specific config path & default creation ---------------------------
def get_default_config_path() -> Path:
    home = Path.home()
    system = platform.system()
    if system == "Windows":
        appdata = os.getenv("APPDATA", home)
        return Path(appdata) / "sequence-llm" / "config.yaml"
    if system == "Darwin":
        return home / "Library" / "Application Support" / "sequence-llm" / "config.yaml"
    # Linux / other
    return home / ".config" / "sequence-llm" / "config.yaml"


DEFAULT_CONFIG_YAML = """# Sequence-LLM configuration for llama.cpp
# Path to llama-server executable
llama_server: "E:\\\\LLama\\\\llama-server.exe"

# Default parameters applied to all profiles (can be overridden per-profile)
defaults:
  threads: 6            # CPU threads to use for inference
  threads_batch: 8      # Threads for batched inference
  batch_size: 512       # Max batch size for processing

# Model profiles - sequential execution (stop one before starting another)
profiles:
  brain:
    name: "Brain (GLM-4.7-Flash)"
    model_path: "E:\\\\LLama\\\\models\\\\GLM-4.7-Flash-Abliterated-i1\\\\Huihui-GLM-4.7-Flash-abliterated.i1-IQ3_XS.gguf"
    port: 8081
    ctx_size: 16384
    threads: 6
    ngl: 0              # Number of GPU layers (0 = CPU only)
    temperature: 0.7
    top_p: 0.95

  coder:
    name: "Coder (Qwen2.5-Coder-7B)"
    model_path: "E:\\\\LLama\\\\models\\\\Qwen2.5-Coder-7B-Instruct-abliterated\\\\Qwen2.5-Coder-7B-Instruct-abliterated.Q4_K_M.gguf"
    port: 8082
    ctx_size: 32768
    threads: 6
    ngl: 0
    temperature: 0.3
    top_p: 0.95

# Default profile to auto-start on CLI launch
default_model: brain
"""


def ensure_default_config(path: Path | None = None) -> Path:
    path = Path(path or get_default_config_path())
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
    return path

