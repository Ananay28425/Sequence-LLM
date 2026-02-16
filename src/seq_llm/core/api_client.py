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
        """Send a non-streaming chat completion request and return JSON."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        payload.update(kwargs)

        response = self.client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    def stream_chat(self, messages: List[Dict[str, str]], model: str = "local"):
        """POST /v1/chat/completions with stream=true and yield text chunks.

        Yields each text chunk emitted by the server (caller responsible for
        assembling tokens into final text).
        """
        payload = {"model": model, "messages": messages, "stream": True}
        with self.client.stream("POST", "/v1/chat/completions", json=payload, timeout=None) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_text():
                # httpx yields text chunks as they arrive; forward them to caller
                yield chunk

    def list_models(self) -> Dict[str, Any]:
        response = self.client.get("/models")
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        try:
            response = self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
