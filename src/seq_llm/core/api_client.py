"""
OpenAI-compatible API client for interacting with LLM servers.
"""

import json
import time
from typing import Any, Dict, List, Optional

import httpx


class APIClient:
    """Client for communicating with OpenAI-compatible LLM servers."""

    def __init__(self, base_url: str, api_key: str = "sk-default"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=None,  # streaming requires no global timeout
        )

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "local",
        stall_timeout: int = 30,
    ):
        """
        Stream chat tokens from server.

        stall_timeout:
            Maximum seconds without receiving data before raising error.
            Prevents infinite hanging when server stops responding.
        """

        payload = {"model": model, "messages": messages, "stream": True}

        last_activity = time.time()

        with self.client.stream("POST", "/v1/chat/completions", json=payload) as resp:
            resp.raise_for_status()

            for line in resp.iter_lines():
                # Stall detection
                if time.time() - last_activity > stall_timeout:
                    raise RuntimeError(
                        f"Stream stalled for {stall_timeout}s — server may be frozen."
                    )

                if not line:
                    continue

                last_activity = time.time()

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
                    continue

                choices = payload.get("choices") or []
                if not choices:
                    continue

                choice = choices[0] or {}
                delta = choice.get("delta") or {}

                text = delta.get("content") if isinstance(delta, dict) else ""

                if not text:
                    text = choice.get("text") or ""

                if not text:
                    message = choice.get("message") or {}
                    if isinstance(message, dict):
                        text = message.get("content") or ""

                if text:
                    yield text

    def health_check(self) -> bool:
        try:
            r = self.client.get("/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
