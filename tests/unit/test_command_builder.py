from pathlib import Path

from seq_llm.config import ModelConfig
from seq_llm.core.command_builder import build_llama_server_command


def test_build_command_uses_canonical_model_and_port_flags(tmp_path):
    llama_server = tmp_path / "llama-server"
    llama_server.write_text("#!/bin/sh\n", encoding="utf-8")
    model = tmp_path / "model.gguf"
    model.write_text("fake", encoding="utf-8")

    profile = ModelConfig(
        name="brain",
        model_type="local",
        endpoint=str(model),
        port=8081,
        ctx_size=4096,
        threads=8,
    )

    cmd = build_llama_server_command(str(llama_server), profile, config_defaults={})

    assert cmd[:5] == [
        str(llama_server),
        "--model",
        str(model),
        "--port",
        "8081",
    ]


def test_build_command_includes_compatible_optional_flags(tmp_path):
    llama_server = tmp_path / "llama-server"
    llama_server.write_text("#!/bin/sh\n", encoding="utf-8")
    model = tmp_path / "model.gguf"
    model.write_text("fake", encoding="utf-8")

    profile = ModelConfig(
        name="brain",
        model_type="local",
        endpoint=str(model),
        port=8081,
        ngl=20,
    )
    # Inject optional fields not present in dataclass to exercise compatibility logic
    profile.threads_batch = 12
    profile.batch_size = 1024

    cmd = build_llama_server_command(
        str(llama_server),
        profile,
        config_defaults={"threads_batch": 10, "batch_size": 512},
        supported_flags={"ngl", "threads-batch", "batch-size"},
    )

    assert "--ngl" in cmd
    assert ["--threads-batch", "12"] == cmd[cmd.index("--threads-batch"):cmd.index("--threads-batch") + 2]
    assert ["--batch-size", "1024"] == cmd[cmd.index("--batch-size"):cmd.index("--batch-size") + 2]
