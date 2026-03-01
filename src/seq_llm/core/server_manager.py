from __future__ import annotations

import datetime
import os
import socket
import subprocess
import time
from typing import Dict, Optional

import psutil
import requests


class ServerManager:
    """
    Responsible for starting, stopping, and monitoring llama-server processes.

    Major responsibilities:
    - Launch subprocess with correct environment
    - Capture logs for debugging
    - Reclaim ports safely
    - Poll health endpoint until server is ready
    """

    LLAMA_SERVER_SIGNATURES = (
        "llama-server",
        "llama_cpp.server",
        "llama.cpp",
    )

    def __init__(self, llama_server_bin: str = "llama-server", health_path: str = "/health"):
        self.llama_server_bin = llama_server_bin
        self.proc: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.health_path = health_path
        self.auto_restart = False
        self.last_logfile: Optional[str] = None

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def _log_dir(self) -> str:
        """Ensure log directory exists and return path."""
        path = os.path.expanduser("~/.seq_llm/logs")
        os.makedirs(path, exist_ok=True)
        return path

    def _create_logfile(self, name: str) -> str:
        """Create a timestamped logfile path."""
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self._log_dir(), f"{name}_{ts}.log")

    # ------------------------------------------------------------------
    # Networking helpers
    # ------------------------------------------------------------------
    def _is_port_open(self, host: str, port: int) -> bool:
        """Check whether TCP port is open."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except Exception:
                return False

    # ------------------------------------------------------------------
    # Process helpers
    # ------------------------------------------------------------------
    def _kill_process(self, pid: int):
        """Terminate process gracefully then force kill if needed."""
        try:
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=5)
        except psutil.NoSuchProcess:
            return
        except psutil.TimeoutExpired:
            try:
                p.kill()
            except Exception:
                pass

    def wait_for_exit(self, pid: int, timeout: int = 20) -> bool:
        """
        Wait for a process to exit.

        This is important on Windows because memory is not released instantly.
        """
        deadline = time.time() + timeout
        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return True

        while time.time() < deadline:
            if not proc.is_running():
                return True
            time.sleep(0.25)

        return False

    def _is_known_llama_server_process(self, process: psutil.Process) -> bool:
        """Detect whether a process looks like llama-server."""
        try:
            candidates = [process.exe(), process.name(), *process.cmdline()]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

        lowered = " ".join(part.lower() for part in candidates if part)
        return any(sig in lowered for sig in self.LLAMA_SERVER_SIGNATURES)

    def _reclaim_port_processes(self, port: int, strict: bool = True):
        """
        Kill processes occupying the given port if they are known llama processes.
        """
        for conn in psutil.net_connections(kind="inet"):
            if not conn.laddr or conn.laddr.port != port:
                continue

            if not conn.pid:
                continue

            try:
                process = psutil.Process(conn.pid)
            except psutil.NoSuchProcess:
                continue

            if self._is_known_llama_server_process(process):
                self._kill_process(conn.pid)
                continue

            if strict:
                raise RuntimeError(
                    f"Port {port} is in use by PID {conn.pid}. "
                    "Refusing to terminate unknown process."
                )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start_cmd(
        self,
        cmd: list[str],
        port: int,
        extra_env: Optional[Dict] = None,
        auto_restart: bool = False,
        strict_port_reclaim: bool = True,
        startup_timeout: int = 60,
    ):
        """
        Start llama-server from command list and wait until healthy.

        Includes:
        - Port reclaim
        - Log capture
        - Health polling
        """

        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)

        # Reclaim port if necessary
        if self._is_port_open("127.0.0.1", port):
            self._reclaim_port_processes(port, strict=strict_port_reclaim)
            time.sleep(3)

        logfile = self._create_logfile("server")
        self.last_logfile = logfile

        log_file_handle = open(logfile, "wb")

        # Launch process
        self.proc = subprocess.Popen(
            cmd,
            stdout=log_file_handle,
            stderr=subprocess.STDOUT,
            env=env,
        )
        self.pid = self.proc.pid
        self.auto_restart = bool(auto_restart)

        print(f"[Sequence-LLM] Server PID {self.pid}")
        print(f"[Sequence-LLM] Logs: {logfile}")

        # Detect early crash
        time.sleep(0.5)
        if self.proc.poll() is not None:
            raise RuntimeError(
                f"Server exited immediately (code {self.proc.returncode}). "
                f"Check logs: {logfile}"
            )

        # Wait for health
        self.wait_for_health(port, timeout=startup_timeout)

    def stop(self):
        """Stop running server."""
        if self.pid:
            self._kill_process(self.pid)
            self.wait_for_exit(self.pid)
            self.proc = None
            self.pid = None

    def is_running(self) -> bool:
        """Check if managed process is alive."""
        if self.pid is None:
            return False
        return psutil.pid_exists(self.pid)

    def wait_for_health(self, port: int, timeout: int = 60, interval: float = 1.0):
        """
        Poll health endpoint until server responds.

        Raises detailed error including logfile location.
        """
        url = f"http://127.0.0.1:{port}{self.health_path}"
        deadline = time.time() + timeout
        backoff = interval

        while time.time() < deadline:
            try:
                r = requests.get(url, timeout=2.0)
                if r.status_code == 200:
                    return True
            except Exception:
                pass

            # Check if process crashed
            if self.proc and self.proc.poll() is not None:
                raise RuntimeError(f"Server crashed during startup. Logs: {self.last_logfile}")

            time.sleep(backoff)
            backoff = min(backoff * 1.5, 5.0)

        raise TimeoutError(
            f"Health check failed for {url} after {timeout}s. " f"Check logs: {self.last_logfile}"
        )
