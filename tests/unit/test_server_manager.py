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


def test_reclaim_port_does_not_kill_foreign_process_by_default(monkeypatch):
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

    with pytest.raises(RuntimeError, match="Refusing to terminate a foreign process in strict reclaim mode"):
        manager._reclaim_port_processes(port=8080)

    assert killed == []


def test_reclaim_port_kills_tracked_llama_server_process(monkeypatch):
    manager = ServerManager()
    target_pid = 4321
    manager.pid = target_pid
    manager.command = ["llama-server", "--port", "8080"]

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

    manager._reclaim_port_processes(port=8080)

    assert killed == [target_pid]


def test_kill_process_timeout_falls_back_to_force_kill(monkeypatch):
    manager = ServerManager()

    class TimeoutProcess:
        def __init__(self):
            self.terminated = False
            self.killed = False

        def terminate(self):
            self.terminated = True

        def wait(self, timeout):
            raise pytest.importorskip("psutil").TimeoutExpired(timeout, pid=1111)

        def kill(self):
            self.killed = True

    proc = TimeoutProcess()
    monkeypatch.setattr("seq_llm.core.server_manager.psutil.Process", lambda pid: proc)

    manager._kill_process(1111)

    assert proc.terminated is True
    assert proc.killed is True
