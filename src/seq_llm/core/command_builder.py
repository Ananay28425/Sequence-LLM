"""Build llama-server command-line arguments from profile configuration."""

from __future__ import annotations

from typing import Any, Dict, List

from seq_llm.config import ModelConfig


def build_llama_server_command(
    llama_server_path: str,
    profile: ModelConfig,
    config_defaults: Dict[str, Any] | None = None,
) -> List[str]:
    """
    Build the complete llama-server command-line arguments from a profile config.
    
    Maps profile fields to llama-server CLI arguments:
    - model_path (in endpoint) -> -m <model_path>
    - port -> --port <port>
    - ctx_size -> --ctx-size <ctx_size>
    - threads -> --threads <threads>
    - ngl -> --ngl <ngl>
    - temperature -> (passed via API, not CLI)
    - top_p -> (passed via API, not CLI)
    
    Args:
        llama_server_path: Path to llama-server executable
        profile: The ModelConfig profile to start
        config_defaults: Global defaults dict (optional, for fallback values)
    
    Returns:
        List of command arguments ready for subprocess.Popen
    
    Example:
        >>> profile = ModelConfig(
        ...     name="brain",
        ...     model_type="local",
        ...     endpoint="E:\\\\path\\\\model.gguf",
        ...     port=8081,
        ...     ctx_size=16384,
        ...     threads=6,
        ... )
        >>> cmd = build_llama_server_command("E:\\\\llama-server.exe", profile)
        >>> # Returns: ["E:\\\\llama-server.exe", "-m", "E:\\\\path\\\\model.gguf", "--port", "8081", ...]
    """
    if config_defaults is None:
        config_defaults = {}
    
    cmd: List[str] = [str(llama_server_path)]
    
    # Model path (required) - stored in endpoint field
    model_path = profile.endpoint
    if not model_path or "://" in model_path:
        # Skip remote models (endpoints with http://, etc.)
        raise ValueError(f"Invalid model path for profile {profile.name}: {model_path}")
    
    cmd.extend(["-m", str(model_path)])
    
    # Port (required in llama-server)
    cmd.extend(["--port", str(profile.port)])
    
    # Context size (ctx-size)
    if profile.ctx_size:
        cmd.extend(["--ctx-size", str(profile.ctx_size)])
    
    # Threads (inference threads)
    if profile.threads:
        cmd.extend(["--threads", str(profile.threads)])
    
    # GPU layers (ngl: 0 = CPU only, useful for RAM-constrained systems)
    cmd.extend(["--ngl", str(profile.ngl)])
    
    # Optional: Batch threads (threads for batched inference) from defaults
    batch_threads = config_defaults.get("threads_batch")
    if batch_threads:
        cmd.extend(["--threads-batch", str(batch_threads)])
    
    # Optional: Batch size from defaults
    batch_size = config_defaults.get("batch_size")
    if batch_size:
        cmd.extend(["--batch-size", str(batch_size)])
    
    return cmd
