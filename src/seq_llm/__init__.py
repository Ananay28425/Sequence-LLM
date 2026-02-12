"""Sequence-LLM: A unified interface for managing and interacting with LLM sequences."""

__version__ = "0.1.0"
__author__ = "Sequence-LLM Contributors"

from seq_llm.cli import main
from seq_llm.config import Config
from seq_llm.core.api_client import APIClient
from seq_llm.core.server_manager import ServerManager

__all__ = [
    "main",
    "Config",
    "APIClient",
    "ServerManager",
]
