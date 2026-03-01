"""Build llama-server command-line arguments from profile_cfg configuration.

Compatibility policy:
- The builder emits the long-form `--model` and `--port` flags first.
- `ServerManager.start_cmd(...)` treats this full command as authoritative.
- `ServerManager.start(...)` owns model/port internally and only accepts
  supplemental args, preserving backwards compatibility for callers that do
  not provide model/port in `args`.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from seq_llm.config import ModelConfig


def build_llama_server_command(
    llama_server_path: str,
    profile_cfg: ModelConfig,
    config_defaults: Optional[Dict[str, Any]] = None,
    supported_flags: Optional[Set[str]] = None,
) -> List[str]:
    """
    Build the complete llama-server command-line arguments from a profile_cfg config.

    - llama_server_path: path to the llama-server executable (string)
    - profile_cfg: ModelConfig instance (must provide endpoint/model_path and port)
    - config_defaults: fallback defaults for threads_batch, batch_size, etc.
    - supported_flags: optional set of flag names the target binary accepts,
      e.g. {"ngl", "threads-batch", "threads", "ctx-size"}. If None, the builder
      acts conservatively (only emits obviously supported flags).

    Returns: a list of command-line tokens suitable for subprocess.Popen([...])
    """
    if config_defaults is None:
        config_defaults = {}

    # Validate binary exists (helpful early error message)
    exe_path = Path(llama_server_path)
    if not exe_path.exists():
        raise FileNotFoundError(f"llama-server binary not found: {llama_server_path}")

    cmd: List[str] = [str(llama_server_path)]

    # Model path (required) - use canonical long flag for compatibility.
    model_path = getattr(profile_cfg, "endpoint", None)
    if not model_path or "://" in model_path:
        raise ValueError(f"Invalid model path for profile {profile_cfg.name}: {model_path}")
    cmd.extend(["--model", str(model_path)])

    # Port (required)
    cmd.extend(["--port", str(profile_cfg.port)])

    # ctx-size
    if getattr(profile_cfg, "ctx_size", None):
        cmd.extend(["--ctx-size", str(profile_cfg.ctx_size)])

    # threads
    if getattr(profile_cfg, "threads", None):
        cmd.extend(["--threads", str(profile_cfg.threads)])

    # ngl: emit only if integer > 0 and supported (if supported_flags is provided)
    ngl = getattr(profile_cfg, "ngl", None)
    if isinstance(ngl, int) and ngl > 0:
        if supported_flags is None or "ngl" in supported_flags:
            cmd.extend(["--ngl", str(ngl)])
        # else: skip silently (binary doesn't support it)

    # threads-batch: profile override first, then defaults
    batch_threads = getattr(profile_cfg, "threads_batch", None) or config_defaults.get("threads_batch")
    if batch_threads:
        # use flag name expected by llama-server
        if supported_flags is None or "threads-batch" in supported_flags:
            cmd.extend(["--threads-batch", str(batch_threads)])

    # batch-size
    batch_size = getattr(profile_cfg, "batch_size", None) or config_defaults.get("batch_size")
    if batch_size:
        if supported_flags is None or "batch-size" in supported_flags:
            cmd.extend(["--batch-size", str(batch_size)])

    # allow arbitrary extra CLI args in profile_cfg (helpful for TPU/HPU wrappers or variant flags)
    extra_args = getattr(profile_cfg, "extra_args", None)
    if extra_args:
        if not isinstance(extra_args, (list, tuple)):
            raise ValueError("profile_cfg.extra_args must be a list of strings")
        cmd.extend([str(x) for x in extra_args])

    return cmd
