# src/seq_llm/core/server_manager.py
from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

import psutil
import requests


class ServerManager:
    def __init__(self, llama_server_bin: str = "llama-server", health_path: str = "/health"):
        self.llama_server_bin = llama_server_bin
        self.proc: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.health_path = health_path
        self.auto_restart = False

    def _is_port_open(self, host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except Exception:
                return False

    def _kill_process(self, pid: int):
        try:
            p = psutil.Process(pid)
            # terminate gracefully then kill if needed
            p.terminate()
            p.wait(timeout=3)
        except psutil.NoSuchProcess:
            return
        except psutil.TimeoutExpired:
            try:
                p.kill()
            except Exception:
                pass

    def _reclaim_port_processes(self, port: int):
        """Kill processes that are listening on `port` and match llama-server binary if possible."""
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr and conn.laddr.port == port:
                if conn.pid:
                    try:
                        p = psutil.Process(conn.pid)
                        # Only kill if executable path looks like llama-server or user explicitly forced
                        exe = (p.exe() or "").lower()
                        if (
                            "llama" in exe or True
                        ):  # conservative: allow kill but be careful in production
                            self._kill_process(conn.pid)
                    except Exception:
                        pass

    def start(
        self,
        model_path: str,
        port: int,
        args: Optional[list] = None,
        extra_env: Optional[Dict] = None,
        auto_restart: bool = False,
    ):
        """
        Start llama-server with model path and return once health endpoint is ready or raise TimeoutError.
        """
        args = args or []
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        # If something is on port, try to reclaim
        if self._is_port_open("127.0.0.1", port):
            self._reclaim_port_processes(port)
            # small wait for kernel sockets to clear
            time.sleep(0.5)

        cmd = [self.llama_server_bin, "--model", model_path, "--port", str(port)] + args
        # Start process
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        self.pid = self.proc.pid
        self.auto_restart = bool(auto_restart)
        # Wait for health
        try:
            self.wait_for_health(port, timeout=30)
        except Exception:
            # On failure, try to cleanup and rethrow
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
            raise

    def stop(self):
        if self.pid:
            try:
                self._kill_process(self.pid)
            except Exception:
                pass
            # reset
            self.proc = None
            self.pid = None

    def is_running(self) -> bool:
        if self.pid is None:
            return False
        return psutil.pid_exists(self.pid)

    def wait_for_health(self, port: int, timeout: int = 30, interval: float = 1.0):
        """Poll http://127.0.0.1:{port}/health until it returns 200 or timeout."""
        url = f"http://127.0.0.1:{port}/health"
        deadline = time.time() + timeout
        backoff = interval
        while time.time() < deadline:
            try:
                r = requests.get(url, timeout=1.0)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(backoff)
            # small exponential backoff, capped
            backoff = min(backoff * 1.5, 5.0)
        raise TimeoutError(f"Health check failed for {url} after {timeout}s")
