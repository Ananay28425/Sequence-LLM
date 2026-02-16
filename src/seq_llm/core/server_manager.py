import subprocess
import os
import time
import logging
from typing import Optional, Sequence, Dict
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class ServerManager:
    """Manage a single llama-server process and its health/state.

    Designed to match unit-test expectations (list command, env merging,
    graceful stop -> kill behavior, health checks via requests.get).
    """

    def __init__(self, server_command: Sequence[str], port: int, timeout: int = 30):
        if not (1 <= int(port) <= 65535):
            raise ValueError("port must be in range 1..65535")

        self.server_command = list(server_command)
        self.port = int(port)
        self.timeout = int(timeout)
        self.process: Optional[subprocess.Popen] = None

    # --- lifecycle -----------------------------------------------------
    def start(self, env_vars: Optional[Dict[str, str]] = None) -> None:
        """Start the server process (non-blocking).

        The caller can use wait_for_ready() to poll health separately.
        """
        if self.process and self.process.poll() is None:
            logger.debug("Process already running")
            return

        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Ensure PORT is set for servers that read it from env
        env.setdefault("PORT", str(self.port))

        logger.debug("Starting: %s", " ".join(str(c) for c in self.server_command))
        self.process = subprocess.Popen(
            self.server_command,
            env=env,
            stdout=None,  # Show output directly to terminal
            stderr=None,  # Show errors directly to terminal
        )

    def stop(self, force: bool = False) -> None:
        """Stop the running process. If force is True, kill immediately."""
        if not self.process:
            return

        try:
            if force:
                self.process.kill()
            else:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
        finally:
            self.process = None

    # --- status / health ------------------------------------------------
    def is_ready(self) -> bool:
        """Return True if the server health endpoint returns 200."""
        try:
            resp = requests.get(f"{self.get_base_url()}/health", timeout=1)
            return resp.status_code == 200
        except Exception:
            return False

    def wait_for_ready(self, timeout: Optional[int] = None) -> bool:
        """Poll the health endpoint every 1s until timeout (seconds)."""
        timeout = timeout if timeout is not None else self.timeout
        start = time.time()
        while time.time() - start < timeout:
            if self.is_ready():
                return True
            time.sleep(1)
        return False

    def get_port(self) -> int:
        return self.port

    def get_base_url(self) -> str:
        return f"http://localhost:{self.port}"

    # --- context manager -----------------------------------------------
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()

