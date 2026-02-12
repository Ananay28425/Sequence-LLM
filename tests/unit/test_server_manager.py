import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from seq_llm.core.server_manager import ServerManager


class TestServerManager(unittest.TestCase):
    """Test cases for ServerManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ServerManager(
            server_command=["python", "-m", "llama_cpp.server"], port=8000, timeout=30
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.manager.process and self.manager.process.poll() is None:
            self.manager.stop()

    @patch('subprocess.Popen')
    def test_start_server(self, mock_popen):
        """Test starting the server."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        self.manager.start()

        mock_popen.assert_called_once()
        self.assertEqual(self.manager.process, mock_process)

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_start_server_with_env_vars(self, mock_sleep, mock_popen):
        """Test starting server with environment variables."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        env_vars = {"MODEL_PATH": "/path/to/model"}

        self.manager.start(env_vars=env_vars)

        call_args = mock_popen.call_args
        self.assertIn("MODEL_PATH", call_args[1]["env"])

    @patch('subprocess.Popen')
    def test_stop_server(self, mock_popen):
        """Test stopping the server."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        self.manager.start()
        self.manager.stop()

        mock_process.terminate.assert_called()

    @patch('subprocess.Popen')
    def test_stop_server_force_kill(self, mock_popen):
        """Test force killing the server."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running
        mock_popen.return_value = mock_process

        self.manager.start()
        self.manager.stop(force=True)

        mock_process.kill.assert_called()

    @patch('requests.get')
    def test_is_ready_true(self, mock_get):
        """Test is_ready returns True when server is up."""
        mock_get.return_value.status_code = 200

        result = self.manager.is_ready()

        self.assertTrue(result)

    @patch('requests.get')
    def test_is_ready_false(self, mock_get):
        """Test is_ready returns False when server is down."""
        mock_get.side_effect = Exception("Connection refused")

        result = self.manager.is_ready()

        self.assertFalse(result)

    @patch('subprocess.Popen')
    @patch('requests.get')
    def test_wait_for_ready(self, mock_get, mock_popen):
        """Test waiting for server to be ready."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        mock_get.return_value.status_code = 200

        self.manager.start()
        result = self.manager.wait_for_ready(timeout=5)

        self.assertTrue(result)

    def test_get_port(self):
        """Test getting the server port."""
        self.assertEqual(self.manager.get_port(), 8000)

    def test_get_base_url(self):
        """Test getting the server base URL."""
        self.assertEqual(self.manager.get_base_url(), "http://localhost:8000")

    def test_server_manager_context_manager(self):
        """Test ServerManager as a context manager."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process

            with ServerManager(server_command=["python", "-m", "test"], port=8001) as manager:
                self.assertIsNotNone(manager.process)

            mock_process.terminate.assert_called()

    @patch('subprocess.Popen')
    def test_server_manager_with_custom_timeout(self, mock_popen):
        """Test ServerManager initialization with custom timeout."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        manager = ServerManager(server_command=["test"], port=9000, timeout=60)

        self.assertEqual(manager.timeout, 60)

    def test_port_validation(self):
        """Test that port number is validated."""
        with self.assertRaises(ValueError):
            ServerManager(server_command=["test"], port=70000)  # Invalid port number

    def test_port_in_valid_range(self):
        """Test that valid port numbers are accepted."""
        for port in [1, 80, 443, 8000, 65535]:
            manager = ServerManager(server_command=["test"], port=port)
            self.assertEqual(manager.port, port)


if __name__ == "__main__":
    unittest.main()
