import sys
import types

if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)

from types import SimpleNamespace

import pytest

from seq_llm.core.server_manager import ServerManager


class FakeProcess:
    def __init__(self, pid: int, exe: str = "", cmdline: list[str] | None = None, name: str = "proc"):
        self.pid = pid
        self._exe = exe
        self._cmdline = cmdline or []
        self._name = name

    def exe(self):
        return self._exe

    def cmdline(self):
        return self._cmdline

    def name(self):
        return self._name


def test_reclaim_port_kills_matching_llama_server(monkeypatch):
    manager = ServerManager()
    target_pid = 4321

    conn = SimpleNamespace(laddr=SimpleNamespace(port=8080), pid=target_pid)
    process = FakeProcess(
        pid=target_pid,
        exe="/usr/local/bin/llama-server",
        cmdline=["llama-server", "--port", "8080"],
        name="llama-server",
    )

    monkeypatch.setattr("seq_llm.core.server_manager.psutil.net_connections", lambda kind: [conn])
    monkeypatch.setattr("seq_llm.core.server_manager.psutil.Process", lambda pid: process)

    killed = []
    monkeypatch.setattr(manager, "_kill_process", lambda pid: killed.append(pid))

    manager._reclaim_port_processes(port=8080, strict=True)

    assert killed == [target_pid]


def test_reclaim_port_refuses_unrelated_process(monkeypatch):
    manager = ServerManager()
    target_pid = 8765

    conn = SimpleNamespace(laddr=SimpleNamespace(port=8080), pid=target_pid)
    process = FakeProcess(
        pid=target_pid,
        exe="/usr/bin/python3",
        cmdline=["python", "app.py"],
        name="python",
    )

    monkeypatch.setattr("seq_llm.core.server_manager.psutil.net_connections", lambda kind: [conn])
    monkeypatch.setattr("seq_llm.core.server_manager.psutil.Process", lambda pid: process)

    killed = []
    monkeypatch.setattr(manager, "_kill_process", lambda pid: killed.append(pid))

    with pytest.raises(RuntimeError, match="Refusing to terminate a non-llama process in strict mode"):
        manager._reclaim_port_processes(port=8080, strict=True)

    assert killed == []


def test_start_fails_cleanly_when_port_conflict_not_reclaimable(monkeypatch):
    manager = ServerManager()

    monkeypatch.setattr(manager, "_is_port_open", lambda host, port: True)
    monkeypatch.setattr(
        manager,
        "_reclaim_port_processes",
        lambda port, strict: (_ for _ in ()).throw(
            RuntimeError(
                "Port 8080 is in use by PID 9988 (python app.py). "
                "Refusing to terminate a non-llama process in strict mode."
            )
        ),
    )

    with pytest.raises(RuntimeError, match="Port 8080 is in use by PID 9988"):
        manager.start(model_path="model.gguf", port=8080)


def test_start_waits_once_with_configured_timeout(monkeypatch):
    manager = ServerManager()

    class DummyProc:
        pid = 1234

        def poll(self):
            return None

        def terminate(self):
            return None

    monkeypatch.setattr(manager, "_is_port_open", lambda host, port: False)
    monkeypatch.setattr("seq_llm.core.server_manager.subprocess.Popen", lambda *args, **kwargs: DummyProc())

    calls = []

    def _wait_for_health(port, timeout, interval=1.0):
        calls.append((port, timeout, interval))
        return True

    monkeypatch.setattr(manager, "wait_for_health", _wait_for_health)

    manager.start(model_path="model.gguf", port=8080, startup_timeout=77)

    assert calls == [(8080, 77, 1.0)]


def test_start_rejects_model_or_port_flags_in_args():
    manager = ServerManager()

    with pytest.raises(ValueError, match="must not include model/port flags"):
        manager.start(model_path="model.gguf", port=8080, args=["--port", "8081"])


def test_start_cmd_uses_explicit_command(monkeypatch):
    manager = ServerManager()

    class DummyProc:
        pid = 4444

        def poll(self):
            return None

        def terminate(self):
            return None

    monkeypatch.setattr(manager, "_is_port_open", lambda host, port: False)

    popen_calls = []

    def _popen(cmd, stdout, stderr, env):
        popen_calls.append(cmd)
        return DummyProc()

    monkeypatch.setattr("seq_llm.core.server_manager.subprocess.Popen", _popen)
    monkeypatch.setattr(manager, "wait_for_health", lambda port, timeout, interval=1.0: True)

    cmd = ["/bin/llama-server", "--model", "x.gguf", "--port", "8089", "--threads", "8"]
    manager.start_cmd(cmd=cmd, port=8089)

    assert popen_calls == [cmd]
