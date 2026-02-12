"""
OpenAI-compatible API client for interacting with LLM servers.
"""

import httpx
from typing import Optional, Any, Dict, List


class APIClient:
    """Client for communicating with OpenAI-compatible LLM servers."""

    def __init__(self, base_url: str, api_key: str = "sk-default"):
        """
        Initialize the API client.

        Args:
            base_url: The base URL of the LLM server (e.g., http://localhost:8000/v1)
            api_key: API key for authentication (default: sk-default)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the server.

        Args:
            model: The model identifier to use
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters to pass to the API

        Returns:
            The API response as a dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        payload.update(kwargs)

        response = self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    def list_models(self) -> Dict[str, Any]:
        """
        List available models on the server.

        Returns:
            The API response containing available models

        Raises:
            httpx.HTTPError: If the request fails
        """
        response = self.client.get("/models")
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """
        Check if the server is healthy and accessible.

        Returns:
            True if the server is accessible, False otherwise
        """
        try:
            response = self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        """Close the HTTP client connection."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
