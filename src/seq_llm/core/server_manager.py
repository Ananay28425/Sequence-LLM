import subprocess
import socket
import time
import os
import signal
from typing import Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ServerManager:
    """Manages lifecycle of local LLM servers (process, port, startup/shutdown)."""

    def __init__(self, server_command: str, port: int, timeout: int = 30):
        """
        Initialize server manager.

        Args:
            server_command: Command to start the server (e.g., "ollama serve")
            port: Port number to run the server on
            timeout: Maximum seconds to wait for server to be ready
        """
        self.server_command = server_command
        self.port = port
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False

    def start(self) -> bool:
        """
        Start the server process.

        Returns:
            True if server started successfully, False otherwise
        """
        if self.is_running:
            logger.warning(f"Server is already running on port {self.port}")
            return True

        try:
            # Set environment variable for port if applicable
            env = os.environ.copy()
            env["PORT"] = str(self.port)

            # Start the server process
            logger.info(f"Starting server: {self.server_command}")
            self.process = subprocess.Popen(
                self.server_command,
                shell=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for server to be ready
            if self._wait_for_server():
                self.is_running = True
                logger.info(f"Server started successfully on port {self.port}")
                return True
            else:
                logger.error(f"Server failed to start within {self.timeout} seconds")
                self.stop()
                return False

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop the server process.

        Returns:
            True if server stopped successfully, False otherwise
        """
        if not self.is_running or self.process is None:
            return True

        try:
            logger.info(f"Stopping server on port {self.port}")

            # Try graceful termination first
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if terminate doesn't work
                logger.warning("Server did not terminate gracefully, forcing kill")
                self.process.kill()
                self.process.wait()

            self.is_running = False
            logger.info("Server stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            return False

    def restart(self) -> bool:
        """
        Restart the server.

        Returns:
            True if restart was successful, False otherwise
        """
        logger.info("Restarting server")
        self.stop()
        time.sleep(1)  # Brief pause between stop and start
        return self.start()

    def is_port_available(self) -> bool:
        """
        Check if the port is available (not in use).

        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", self.port))
                return True
        except OSError:
            return False

    def _wait_for_server(self) -> bool:
        """
        Wait for server to become available (port responds to connections).

        Returns:
            True if server is ready, False if timeout occurs
        """
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(("localhost", self.port))
                    if result == 0:
                        logger.debug(f"Server is responding on port {self.port}")
                        return True
            except Exception:
                pass

            time.sleep(0.5)

        return False

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
