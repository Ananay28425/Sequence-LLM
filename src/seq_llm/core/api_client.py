"""
OpenAI-compatible API client for interacting with LLM servers.
"""

import json
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

        Parses server-sent events and yields normalized text tokens only.
        """
        payload = {"model": model, "messages": messages, "stream": True}
        with self.client.stream("POST", "/v1/chat/completions", json=payload, timeout=None) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue

                if line.startswith("event:"):
                    continue

                if not line.startswith("data:"):
                    continue

                data = line[5:].strip()
                if data == "[DONE]":
                    break

                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    # Ignore malformed event payloads and continue streaming.
                    continue

                choices = payload.get("choices") or []
                if not choices:
                    continue

                choice = choices[0] or {}
                delta = choice.get("delta") or {}

                text = ""
                if isinstance(delta, dict):
                    text = delta.get("content") or ""

                if not text and isinstance(choice, dict):
                    text = choice.get("text") or ""

                if not text and isinstance(choice, dict):
                    message = choice.get("message") or {}
                    if isinstance(message, dict):
                        text = message.get("content") or ""

                if text:
                    yield text

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
