import sys
import types

# Minimal stub so seq_llm.core.server_manager can import in test env
if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)

from pathlib import Path

from seq_llm import cli
from seq_llm.config import Config


def test_run_first_time_setup_persists_user_selections(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("server:\n  host: 127.0.0.1\n", encoding="utf-8")

    state = cli.CLIState()
    assert state.load_config(config_path)
    cli.state = state

    candidate_models = [
        {"path": str(tmp_path / "brain.gguf"), "size_gb": 2.0},
        {"path": str(tmp_path / "coder.gguf"), "size_gb": 4.0},
    ]

    answers = iter([
        str(tmp_path / "llama-server"),  # llama_server path
        "2",  # brain -> candidate #2
        "1",  # coder -> candidate #1
    ])

    monkeypatch.setattr(cli, "discover_models", lambda: candidate_models)
    monkeypatch.setattr(cli.console, "input", lambda _prompt: next(answers))

    assert cli.run_first_time_setup() is True

    saved = Config.from_yaml(config_path)
    assert saved.llama_server == str(tmp_path / "llama-server")
    assert saved.get_model("brain") is not None
    assert saved.get_model("coder") is not None
    assert saved.get_model("brain").endpoint == str(tmp_path / "coder.gguf")
    assert saved.get_model("coder").endpoint == str(tmp_path / "brain.gguf")


def test_main_triggers_first_run_then_continues_startup(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("server:\n  host: 127.0.0.1\n", encoding="utf-8")

    state = cli.CLIState()
    cli.state = state

    # Load our local config path instead of touching user config.
    monkeypatch.setattr(cli, "ensure_default_config", lambda: config_path)

    candidate_models = [
        {"path": str(tmp_path / "brain.gguf"), "size_gb": 2.0},
        {"path": str(tmp_path / "coder.gguf"), "size_gb": 4.0},
    ]
    answers = iter([
        str(tmp_path / "llama-server"),
        "1",
        "2",
        "/quit",
    ])

    start_calls = []

    def fake_start_profile(profile_name: str) -> bool:
        start_calls.append(profile_name)
        return True

    monkeypatch.setattr(cli, "discover_models", lambda: candidate_models)
    monkeypatch.setattr(cli.console, "input", lambda _prompt: next(answers))
    monkeypatch.setattr(cli.CLIState, "start_profile", lambda self, profile: fake_start_profile(profile))

    cli.main()

    saved = Config.from_yaml(config_path)
    assert saved.get_model("brain") is not None
    assert saved.get_model("coder") is not None
    assert start_calls == ["brain"]
