import sys
import types

# Minimal stub so seq_llm.core.server_manager can import in test env
if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)

from pathlib import Path
from unittest.mock import Mock

from seq_llm.cli import CLIState
from seq_llm.config import Config, ModelConfig, ServerConfig


def _make_state(tmp_path: Path) -> tuple[CLIState, Config, Path, Path]:
    llama_server = tmp_path / "llama-server"
    llama_server.write_text("#!/bin/sh\n", encoding="utf-8")
    model = tmp_path / "model.gguf"
    model.write_text("fake model", encoding="utf-8")

    cfg = Config(
        server=ServerConfig(),
        llama_server=str(llama_server),
        defaults={"threads": 4},
        models={
            "brain": ModelConfig(
                name="brain",
                model_type="local",
                endpoint=str(model),
                port=8081,
            )
        },
    )

    state = CLIState()
    state.config = cfg
    state.config_path = tmp_path / "config.yaml"
    return state, cfg, llama_server, model


def test_start_profile_happy_path(monkeypatch, tmp_path):
    state, cfg, _, model = _make_state(tmp_path)

    manager = Mock()
    manager.start_cmd = Mock()
    manager.wait_for_health = Mock(return_value=True)
    manager.stop = Mock()

    monkeypatch.setattr("seq_llm.cli.ServerManager", lambda llama_server_bin: manager)
    monkeypatch.setattr(
        "seq_llm.cli.build_llama_server_command",
        lambda llama_server, profile, defaults: [
            llama_server,
            "--model",
            str(model),
            "--port",
            str(profile.port),
            "--ctx-size",
            "4096",
            "--threads",
            "8",
        ],
    )

    result = state.start_profile("brain")

    assert result is True
    manager.start_cmd.assert_called_once_with(
        cmd=[
            cfg.llama_server,
            "--model",
            cfg.get_model("brain").endpoint,
            "--port",
            "8081",
            "--ctx-size",
            "4096",
            "--threads",
            "8",
        ],
        port=8081,
        startup_timeout=120,
    )
    manager.wait_for_health.assert_not_called()
    assert state.active_profile == "brain"


def test_start_profile_error_path_stops_manager(monkeypatch, tmp_path):
    state, cfg, _, model = _make_state(tmp_path)

    manager = Mock()
    manager.start_cmd = Mock(side_effect=TimeoutError("health timeout"))
    manager.wait_for_health = Mock()
    manager.stop = Mock()

    monkeypatch.setattr("seq_llm.cli.ServerManager", lambda llama_server_bin: manager)
    monkeypatch.setattr(
        "seq_llm.cli.build_llama_server_command",
        lambda llama_server, profile, defaults: [
            llama_server,
            "--model",
            str(model),
            "--port",
            str(profile.port),
            "--ctx-size",
            "4096",
        ],
    )

    result = state.start_profile("brain")

    assert result is False
    manager.start_cmd.assert_called_once_with(
        cmd=[
            cfg.llama_server,
            "--model",
            cfg.get_model("brain").endpoint,
            "--port",
            "8081",
            "--ctx-size",
            "4096",
        ],
        port=8081,
        startup_timeout=120,
    )
    manager.wait_for_health.assert_not_called()
    manager.stop.assert_called_once()
    assert state.manager is None
    assert state.active_profile is None


def test_start_profile_restart_uses_shorter_timeout(monkeypatch, tmp_path):
    state, cfg, _, model = _make_state(tmp_path)
    state.active_profile = "brain"

    old_manager = Mock()
    old_manager.stop = Mock()
    state.manager = old_manager

    manager = Mock()
    manager.start_cmd = Mock()
    manager.wait_for_health = Mock()
    manager.stop = Mock()

    monkeypatch.setattr("seq_llm.cli.ServerManager", lambda llama_server_bin: manager)
    monkeypatch.setattr(
        "seq_llm.cli.build_llama_server_command",
        lambda llama_server, profile, defaults: [
            llama_server,
            "--model",
            str(model),
            "--port",
            str(profile.port),
            "--ctx-size",
            "4096",
        ],
    )

    result = state.start_profile("brain")

    assert result is True
    old_manager.stop.assert_called_once()
    manager.start_cmd.assert_called_once_with(
        cmd=[
            cfg.llama_server,
            "--model",
            cfg.get_model("brain").endpoint,
            "--port",
            "8081",
            "--ctx-size",
            "4096",
        ],
        port=8081,
        startup_timeout=60,
    )
    manager.wait_for_health.assert_not_called()
